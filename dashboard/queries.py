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

import db_conn
import pandas as pd
import textwrap


def GetTracks():
  select_statement = textwrap.dedent("""
  SELECT DISTINCT track
  FROM sessions
  """)
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)['track']


def GetSessions():
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


def GetLapsData(lap_ids):
  select_statement = textwrap.dedent("""
    SELECT *
    FROM POINTS
    JOIN laps ON points.lap_id = laps.id
    WHERE lap_id IN %(lap_ids)s
    """)
  lap_ids = tuple(str(lap_id) for lap_id in lap_ids)
  df = pd.io.sql.read_sql(
      select_statement,
      db_conn.POOL.connect(),
      params={'lap_ids': lap_ids})
  df['front_brake_pressure_percentage'] = (
    df['front_brake_pressure_voltage'] /
    df['front_brake_pressure_voltage'].max())
  df['rear_brake_pressure_percentage'] = (
    df['rear_brake_pressure_voltage'] /
    df['rear_brake_pressure_voltage'].max())
  df['gsum'] = df['accelerometer_x'].abs() + df['accelerometer_y'].abs()
  df.rename(columns={'number': 'lap_number'}, inplace=True)
  df.sort_values(by='elapsed_distance_m', inplace=True)
  return df


def GetPointsColumns():
  select_statement = textwrap.dedent("""
  SELECT column_name
  FROM information_schema.columns
  WHERE table_name = 'points'
  """)
  conn = db_conn.POOL.connect()
  resp = conn.execute(select_statement)
  columns = [row[0] for row in resp.fetchall()]
  columns.extend([
    'front_brake_pressure_percentage',
    'rear_brake_pressure_percentage',
    'racing_line',
    'gsum'])
  columns.remove('lat')
  columns.remove('lon')
  return columns
