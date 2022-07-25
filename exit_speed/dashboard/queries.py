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
from typing import Text
from typing import Tuple
from typing import Set

import pandas as pd
from psycopg2 import sql

from exit_speed import postgres
from exit_speed import tracks


TABLES = ('accelerometer', 'gps', 'gyroscope', 'labjack', 'wbo2')


def GetTracks() -> List[Text]:
  return [track.name for track in tracks.TRACK_LIST]


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


def GetTimeDelta(lap_ids: List[int]) -> pd.DataFrame:
  select_statement = textwrap.dedent("""
    SELECT
      a.elapsed_distance_m,
      b.elapsed_duration_ns - a.elapsed_duration_ns AS time_delta,
      b.number AS lap_number
    FROM (
      SELECT
        elapsed_duration_ns,
        ROUND(CAST(elapsed_distance_m AS numeric), 0) as elapsed_distance_m
      FROM points
      JOIN laps ON laps.id=points.lap_id
      WHERE id = %(lap_id_a)s
    ) AS a INNER JOIN (
      SELECT
        elapsed_duration_ns,
        ROUND(CAST(elapsed_distance_m AS numeric), 0) as elapsed_distance_m,
        number
      FROM points
      JOIN laps ON laps.id=points.lap_id
      WHERE id = %(lap_id_b)s
      ) as b
    ON a.elapsed_distance_m = b.elapsed_distance_m
    """)
  lap_id_a = lap_ids[0]
  lap_dfs = []
  with postgres.ConnectToDB() as conn:
    for lap_id in lap_ids[1:]:
      df = pd.io.sql.read_sql(
          select_statement,
          conn,
          params={'lap_id_a': str(lap_id_a),
                  'lap_id_b': str(lap_id)})
      df['lap_id'] = lap_id
      lap_dfs.append(df)
  combined_df = pd.concat(lap_dfs)
  combined_df.sort_values(by='elapsed_distance_m', inplace=True)
  return combined_df


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


def GetPointsColumns() -> Set[Text]:
  columns = set()
  table_columns = GetTableColumns()
  for tc in table_columns.values():
    columns.update(tc)
  columns.remove('lat')
  columns.remove('lon')
  columns.remove('time')
  return columns


def GetColumnsToQuery(point_values: List[Text]) -> List[Text]:
  all_columns = GetPointsColumns()
  # Only select columns that map to point_values.
  columns = set(point_values).intersection(set(all_columns))
  # Columns used for graph labels and should always be included.
  columns.update(['elapsed_distance_m', 'number', 'lap_id'])
  if ('front_brake_pressure_percentage' in point_values or
      'rear_brake_pressure_percentage' in point_values):
    columns.update(['front_brake_pressure_voltage',
                    'rear_brake_pressure_voltage'])
  if 'gsum' in point_values:
    columns.update(['accelerometer_x', 'accelerometer_y', 'accelerometer_z'])
  if 'racing_line' in point_values:
    columns.update(['lat', 'lon'])
  return columns


def GetTableData(table_name: Text,
								 columns: List[Text],
								 start_time: datetime.datetime,
								 end_time: datetime.datetime) -> pd.DataFrame:
  select_statement = textwrap.dedent("""
    SELECT {columns}
    FROM {table}
    WHERE time >= %(start_time)s and time <= %(end_time)s
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


def GetLapData(columns: List[Text],
							 start_time: datetime.datetime,
							 end_time: datetime.datetime) -> pd.DataFrame:
  table_dfs = []
  for table_name, table_columns in GetTableColumns().items():
    # Only select columns that the table contains.
    columns_to_query = set(columns).intersection(set(table_columns))
    columns_to_query.add('time')
    table_dfs.append(
        GetTableData(table_name, columns_to_query, start_time, end_time))
  return pd.concat(table_dfs)


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


def GetLapsData(lap_ids: List[int], point_values: List[Text]) -> pd.DataFrame:
  columns = GetColumnsToQuery(point_values)
  lap_dfs = []
  for lap_id in lap_ids:
    start_time, end_time = GetLapStartEndTimes(lap_id)
    lap_dfs.append(GetLapData(columns, start_time, end_time))
  df = pd.concat(lap_dfs)
  #df.sort_values(by='elapsed_distance_m', inplace=True)
  df['front_brake_pressure_percentage'] = (
    df['front_brake_pressure_voltage'] /
    df['front_brake_pressure_voltage'].max())
  df['rear_brake_pressure_percentage'] = (
    df['rear_brake_pressure_voltage'] /
    df['rear_brake_pressure_voltage'].max())
  df['gsum'] = df['accelerometer_x'].abs() + df['accelerometer_y'].abs()
  #df.rename(columns={'number': 'lap_number'}, inplace=True)
  df['elapsed_duration_ms'] = df['time'] - min(df['time'])
  return df


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
