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
import pandas as pd
import gps
from exit_speed import postgres
from exit_speed import tracks
from psycopg2 import sql

TABLES = ('accelerometer', 'ecu', 'egts', 'gps', 'gyroscope', 'labjack', 'pdm')


def GetTracks() -> List[Text]:
  return [track.name for track in tracks.TRACK_LIST]


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
  if 'lat' in columns: columns.remove('lat')
  if 'lon' in columns: columns.remove('lon')
  if 'time' in columns: columns.remove('time')
  columns.add('gsum')
  columns.add('time_delta')
  return columns


def CalcTimeDeltas(first_lap: pd.DataFrame,
                   df: pd.DataFrame) -> List[float]:
  """Calculates the time delta between the first lap and the current lap."""
  time_deltas = []
  first_lap_index = 0
  for row in df.itertuples():
    while (first_lap_index < len(first_lap) - 1 and
           first_lap.iloc[first_lap_index].elapsed_distance_m <
           row.elapsed_distance_m):
      first_lap_index += 1
    delta = (row.elapsed_duration_ns -
             first_lap.iloc[first_lap_index].elapsed_duration_ns)
    time_deltas.append(delta.total_seconds() * 1000)  # Convert to milliseconds
  return time_deltas


def GetSessions() -> pd.DataFrame:
  select_statement = textwrap.dedent("""
  SELECT
    TO_CHAR((duration_ns / 1e6 || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.number AS lap_number,
    track,
    sessions.id AS session_id
  FROM laps
  JOIN sessions ON laps.session_id = sessions.id
  WHERE
    duration_ns IS NOT NULL
  ORDER BY lap_time ASC
  """)
  with postgres.ConnectToDB() as conn:
    return pd.io.sql.read_sql(select_statement, conn)


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
      print(cursor.mogrify(query.as_string(cursor),
                           {'start_time': start_time,
                            'end_time': end_time}).decode('utf-8'))
      df = pd.io.sql.read_sql(
          query.as_string(cursor),
          conn,
          params={'start_time': start_time,
                  'end_time': end_time})
      return df 


def GetLapData(columns: Set[Text],
               start_time: datetime.datetime,
               end_time: datetime.datetime) -> pd.DataFrame:
  df = None
  for table_name, table_columns in GetTableColumns().items():
    # Only select columns that the table contains.
    columns_to_query = set(columns).intersection(set(table_columns))
    if table_name == 'gps':
      columns_to_query.update(['lat', 'lon'])
    if columns_to_query:
      table_df = GetTableData(table_name, columns_to_query,
                              start_time, end_time)
      if table_df.empty:
        continue
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
        print('~' * 80)
        print(df.dtypes)
        print(df.head())
        print('~' * 80)
        print(table_df.dtypes)
        print(table_df.head())
        print('~' * 80)
        df = pd.merge_asof(df, table_df, on='time')
      else:
        df = table_df
  if df is not None:
    df['elapsed_duration_ns'] = (
        df['time'] - df['time'].min())
    df.bfill(inplace=True)
    if 'elapsed_distance_m' in df.columns:
      df.sort_values(by='elapsed_distance_m', inplace=True)
  return df


def GetLapTableData(
    session_id: int, 
    lap_number: int) -> Tuple[datetime.datetime, datetime.datetime]:
  select_statement = textwrap.dedent("""
  SELECT start_time, end_time
  FROM laps
  WHERE session_id = %s AND number = %s
  """)
  with postgres.ConnectToDB() as conn:
    with conn.cursor() as cursor:
      cursor.execute(select_statement, (session_id, lap_number))
      return cursor.fetchone()
