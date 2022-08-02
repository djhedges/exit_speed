# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Dashboard queries."""
import datetime
import textwrap
from typing import Dict
from typing import List
from typing import Set
from typing import Text
from typing import Tuple

import funcy
import gps
import pandas as pd
from absl import logging
from psycopg2 import sql

from exit_speed import postgres
from exit_speed import tracks


TABLES = ('accelerometer', 'gps', 'gyroscope', 'labjack', 'wbo2')


def GetTracks() -> List[Text]:
  return [track.name for track in tracks.TRACK_LIST]


@funcy.log_durations(logging.debug)
def GetSessions() -> pd.DataFrame:
  select_statement = textwrap.dedent("""
  SELECT
    TO_CHAR((duration_ns / 1e6 || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.id,
    laps.number AS lap_number,
    track
  FROM laps
  JOIN sessions ON laps.session_id=sessions.id
  WHERE
    duration_ns IS NOT null AND
    duration_ns < 8.64e+13
  GROUP BY sessions.id, track, sessions.time, laps.id, laps.number, lap_time, laps.duration_ns
  """)
  with postgres.ConnectToDB() as conn:
    return pd.io.sql.read_sql(select_statement, conn)


@funcy.log_durations(logging.debug)
def GetTableColumns() -> Dict[Text, List[Text]]:
  table_columns = {}
  for table in TABLES:
    select_statement = textwrap.dedent("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = %s
    """)
    with postgres.ConnectToDB() as conn:
      with conn.cursor() as cursor:
        cursor.execute(select_statement, (table,))
        table_columns[table] = [row[0] for row in cursor.fetchall()]
  return table_columns


@funcy.log_durations(logging.debug)
def GetPointsColumns() -> Set[Text]:
  columns = set()
  table_columns = GetTableColumns()
  for tc in table_columns.values():
    columns.update(tc)
  columns.remove('lat')
  columns.remove('lon')
  columns.remove('time')
  return columns


@funcy.log_durations(logging.debug)
def GetColumnsToQuery(point_values: List[Text]) -> Set[Text]:
  all_columns = GetPointsColumns()
  # Only select columns that map to point_values.
  columns = set(point_values).intersection(set(all_columns))
  # Columns used for graph labels and should always be included.
  columns.update(['elapsed_distance_m', 'number', 'lap_id', 'lat', 'lon'])
  if ('front_brake_pressure_percentage' in point_values or
      'rear_brake_pressure_percentage' in point_values):
    columns.update(['front_brake_pressure_voltage',
                    'rear_brake_pressure_voltage'])
  if 'gsum' in point_values:
    columns.update(['accelerometer_x', 'accelerometer_y'])
  if 'racing_line' in point_values:
    columns.update(['lat', 'lon'])
  if 'speed_mph' in point_values:
    columns.add('speed_ms')
  return columns


@funcy.log_durations(logging.debug)
def GetTableData(table_name: Text,
                 columns: Set[Text],
                 start_time: datetime.datetime,
                 end_time: datetime.datetime) -> pd.DataFrame:
  select_statement = textwrap.dedent("""
    SELECT time, {columns}
    FROM {table}
    WHERE time >= %(start_time)s and time <= %(end_time)s
    ORDER BY time
    """)
  query = sql.SQL(select_statement).format(
      columns=sql.SQL(',').join(
          [sql.Identifier(col) for col in columns]),
      table=sql.SQL(table_name))
  with postgres.ConnectToDB() as conn:
    with conn.cursor() as cursor:
      return pd.io.sql.read_sql(
          query.as_string(cursor),
          conn,
          params={'start_time': start_time,
                  'end_time': end_time})


@funcy.log_durations(logging.debug)
def GetLapData(columns: Set[Text],
               start_time: datetime.datetime,
               end_time: datetime.datetime) -> pd.DataFrame:
  df = None
  for table_name, table_columns in GetTableColumns().items():
    # Only select columns that the table contains.
    columns_to_query = set(columns).intersection(set(table_columns))
    if columns_to_query:
      table_df = GetTableData(table_name, columns_to_query,
                              start_time, end_time)
      if table_name == 'gps':
        elapsed_distance_col = []
        elapsed_distance = 0
        prior_row = None
        for row in table_df.itertuples():
          if prior_row:
            elapsed_distance += gps.EarthDistanceSmall(
                (row.lat, row.lon),
                (prior_row.lat, prior_row.lon))
          elapsed_distance_col.append(elapsed_distance)
          prior_row = row
        table_df['elapsed_distance_m'] = elapsed_distance_col
      if df is not None:
        df = pd.merge_asof(df, table_df, on='time')
      else:
        df = table_df
  if df is not None:
    df['elapsed_duration_ns'] = (
        df['time'] - df['time'].min())  #pytype: disable=attribute-error
    df.interpolate(inplace=True)
    df.sort_values(by='elapsed_distance_m', inplace=True)
  return df


@funcy.log_durations(logging.debug)
def GetLapStartEndTimes(
    lap_id: int) -> Tuple[datetime.datetime, datetime.datetime]:
  select_statement = textwrap.dedent("""
  SELECT start_time, end_time
  FROM laps
  WHERE id = %s
  """)
  with postgres.ConnectToDB() as conn:
    with conn.cursor() as cursor:
      cursor.execute(select_statement, (lap_id,))
      return cursor.fetchone()


@funcy.log_durations(logging.debug)
def CalcTimeDeltas(first_lap: pd.DataFrame,
                   df: pd.DataFrame) -> List[float]:
  time_deltas = []
  first_lap_index = 0
  for row in df.itertuples():
    while (first_lap_index < len(first_lap) - 1 and
           first_lap.iloc[first_lap_index].elapsed_distance_m <
           row.elapsed_distance_m):
      first_lap_index += 1
    delta_ns = (row.elapsed_duration_ns -
                first_lap.iloc[first_lap_index].elapsed_duration_ns)
    time_deltas.append(delta_ns / 1e6)
  return time_deltas


@funcy.log_durations(logging.debug)
def GetLapsData(lap_ids: List[int], point_values: List[Text]) -> pd.DataFrame:
  columns = GetColumnsToQuery(point_values)
  lap_dfs = []
  for lap_id in lap_ids:
    start_time, end_time = GetLapStartEndTimes(lap_id)
    lap_df = GetLapData(columns, start_time, end_time)
    lap_df['lap_id'] = lap_id
    if lap_dfs and 'time_delta' in point_values:
      lap_df['time_delta'] = CalcTimeDeltas(lap_dfs[0], lap_df)
    lap_dfs.append(lap_df)
  df = pd.concat(lap_dfs)
  if 'front_brake_pressure_percentage' in point_values:
    df['front_brake_pressure_percentage'] = (
      df['front_brake_pressure_voltage'] /
      df['front_brake_pressure_voltage'].max())
  if 'rear_brake_pressure_percentage' in point_values:
    df['rear_brake_pressure_percentage'] = (
      df['rear_brake_pressure_voltage'] /
      df['rear_brake_pressure_voltage'].max())
  if 'gsum' in point_values:
    df['gsum'] = df['accelerometer_x'].abs() + df['accelerometer_y'].abs()
  if 'speed_mph' in point_values:
    df['speed_mph'] = df['speed_ms'] * 2.23694
  return df


@funcy.log_durations(logging.debug)
def GetLiveData(start_time: datetime.datetime, point_values: List[Text]):
  all_columns = GetPointsColumns()
  # Only select columns that map to point_values.
  columns = set(point_values).intersection(set(all_columns))
  # Columns used for graph labels and should always be included.
  columns.update(['time', 'number', 'lap_id'])
  select_statement = textwrap.dedent("""
    SELECT {columns}
    FROM points
    JOIN laps ON points.lap_id = laps.id
    WHERE
      time > %(start_time)s
    """)
  query = sql.SQL(select_statement).format(
      columns=sql.SQL(',').join(
          [sql.Identifier(col) for col in columns]))
  with postgres.ConnectToDB() as conn:
    with conn.cursor() as cursor:
      df = pd.io.sql.read_sql(
          query.as_string(cursor),
          conn,
          params={'start_time': start_time})
  df.sort_values(by='time', inplace=True)
  df.rename(columns={'number': 'lap_number'}, inplace=True)
  return df
