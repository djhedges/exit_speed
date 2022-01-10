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
from typing import List
from typing import Text

import pandas as pd
from psycopg2 import sql

from exit_speed.dashboard import db_conn


def GetTracks() -> pd.DataFrame:
  select_statement = textwrap.dedent("""
  SELECT DISTINCT track
  FROM sessions
  """)
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)['track']


def GetSessions() -> pd.DataFrame:
  select_statement = textwrap.dedent("""
  SELECT
    TO_CHAR((duration_ms || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.id,
    laps.number AS lap_number,
    track,
    (count(points.time)::float / (duration_ms::float / 1000.0)) as points_per_second
  FROM laps
  JOIN points ON laps.id=points.lap_id
  JOIN sessions ON laps.session_id=sessions.id
  WHERE duration_ms IS NOT null
  GROUP BY sessions.id, track, sessions.time, laps.id, laps.number, lap_time, laps.duration_ms
  """)
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)


def GetTimeDelta(lap_ids: List[int]) -> pd.DataFrame:
  select_statement = textwrap.dedent("""
    SELECT
      a.elapsed_distance_m,
      b.elapsed_duration_ms - a.elapsed_duration_ms AS time_delta,
      b.number AS lap_number
    FROM (
      SELECT
        elapsed_duration_ms,
        ROUND(CAST(elapsed_distance_m AS numeric), 0) as elapsed_distance_m
      FROM points
      JOIN laps ON laps.id=points.lap_id
      WHERE lap_id = %(lap_id_a)s
    ) AS a INNER JOIN (
      SELECT
        elapsed_duration_ms,
        ROUND(CAST(elapsed_distance_m AS numeric), 0) as elapsed_distance_m,
        number
      FROM points
      JOIN laps ON laps.id=points.lap_id
      WHERE lap_id = %(lap_id_b)s
      ) as b
    ON a.elapsed_distance_m = b.elapsed_distance_m
    """)
  lap_id_a = lap_ids[0]
  lap_dfs = []
  for lap_id in lap_ids[1:]:
    df = pd.io.sql.read_sql(
        select_statement,
        db_conn.POOL.connect(),
        params={'lap_id_a': str(lap_id_a),
                'lap_id_b': str(lap_id)})
    df['lap_id'] = lap_id
    lap_dfs.append(df)
  combined_df = pd.concat(lap_dfs)
  combined_df.sort_values(by='elapsed_distance_m', inplace=True)
  return combined_df


def GetPointsColumns() -> List[Text]:
  select_statement = textwrap.dedent("""
  SELECT column_name
  FROM information_schema.columns
  WHERE table_name = 'points'
  """)
  conn = db_conn.POOL.connect()
  resp = conn.execute(select_statement)
  columns = [row[0] for row in resp.fetchall()]
  columns.remove('lat')
  columns.remove('lon')
  return columns


def GetLapsData(lap_ids: List[int], point_values: List[Text]) -> pd.DataFrame:
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
  select_statement = textwrap.dedent("""
    SELECT {columns}
    FROM points
    JOIN laps ON points.lap_id = laps.id
    WHERE lap_id IN %(lap_ids)s
    """)
  query = sql.SQL(select_statement).format(
      columns=sql.SQL(',').join(
          [sql.Identifier(col) for col in columns]))
  raw_conn = db_conn.POOL.raw_connection()
  df = pd.io.sql.read_sql(
      query.as_string(raw_conn.cursor()),
      db_conn.POOL.connect(),
      params={'lap_ids': tuple(str(lap_id) for lap_id in lap_ids)})
  df.sort_values(by='elapsed_distance_m', inplace=True)
  df['front_brake_pressure_percentage'] = (
    df['front_brake_pressure_voltage'] /
    df['front_brake_pressure_voltage'].max())
  df['rear_brake_pressure_percentage'] = (
    df['rear_brake_pressure_voltage'] /
    df['rear_brake_pressure_voltage'].max())
  df['gsum'] = df['accelerometer_x'].abs() + df['accelerometer_y'].abs()
  df.rename(columns={'number': 'lap_number'}, inplace=True)
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
  raw_conn = db_conn.POOL.raw_connection()
  df = pd.io.sql.read_sql(
      query.as_string(raw_conn.cursor()),
      db_conn.POOL.connect(),
      params={'start_time': start_time})
  df.sort_values(by='time', inplace=True)
  df.rename(columns={'number': 'lap_number'}, inplace=True)
  return df
