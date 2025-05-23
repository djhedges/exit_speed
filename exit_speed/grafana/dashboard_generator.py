#!/usr/bin/python3
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
"""Library for generating Grafana live dashboards."""
import textwrap
from typing import Text
from typing import Tuple

from grafanalib import core
from psycopg2 import sql

from exit_speed import postgres


class Generator(object):
  """Generates Grafana dashboards for live Exit Speed data."""

  def __init__(self, title: Text):
    self.title = title
    self.panels = []

  def AddPanel(self, panel: core.Panel):
    panel.gridPos=core.GridPos(
        h=8,
        w=12,
        # First bit of panel length.  Alternates between 0 & 1.
        x=bin(len(self.panels))[-1] * 12,
        y=(len(self.panels) // 2) * 8,
    )
    self.panels.append(panel)

  def AddWorldMapPanel(self):
    self.AddPanel(
        core.Worldmap(
            title='GPS Location',
            targets=[
                core.SqlTarget(
                    rawSql=textwrap.dedent("""
                    SELECT
                      time,
                      extract(second FROM (time + '2s' - NOW())) AS Value,
                      geohash
                    FROM points
                    WHERE
                      geohash != '' AND
                      $__timeFilter(time)
                    ORDER BY time
                    """),
                    format=core.TABLE_TARGET_FORMAT,
                ),
            ],
            circleMinSize=1,
            circleMaxSize=1,
            locationData='geohash',
            mapCenter='Last GeoHash',
            initialZoom=15,
            aggregation='current',
            thresholds='1',
            thresholdColors=['#5794F2', '#73BF69'],
        )
    )

  def AddLapTimesTable(self):
    select_statement = textwrap.dedent("""
        SELECT
          track,
          TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') AS session_time,
          sessions.id AS session_id,
          laps.number AS lap_number,
          TO_CHAR((end_time - start_time || 'millisecond')::interval, 'MI:SS:MS') AS lap_time
        FROM laps
        JOIN sessions ON laps.session_id=sessions.id
        WHERE
          $__timeFilter(laps.start_time)
        GROUP BY sessions.id, session_time, track, laps.number, lap_time
        ORDER BY sessions.id, session_time, track, laps.number, lap_time
    """)
    self.AddPanel(
        core.Table(
            title='Lap Times',
            targets=[core.SqlTarget(
                rawSql=select_statement,
                format=core.TABLE_TARGET_FORMAT
            )],
        )
    )

  def AddGraphPanel(self, title: Text, raw_sql: Text, y_axis_title: Text):
    self.AddPanel(
        core.Graph(
            title=title,
            targets=[
                core.SqlTarget(
                    rawSql=raw_sql,
                    format=core.TABLE_TARGET_FORMAT,
                ),
            ],
            yAxes=core.YAxes(
                core.YAxis(format=y_axis_title),
            ),
        )
    )

  def AddPointPanel(self,
										title: Text,
										table_name: Text,
										point_values: Tuple[Text],
										y_axis_title: Text):
    select_statement = textwrap.dedent("""
        SELECT
          time,
          {columns}
        FROM {table_name}
        WHERE  $__timeFilter(time)
        ORDER BY time
        """)
    query = sql.SQL(select_statement).format(
            table_name=sql.Identifier(table_name),
            columns=sql.SQL(',').join(
                [sql.Identifier(col) for col in point_values]))
    with postgres.ConnectToDB() as conn:
      self.AddGraphPanel(title, query.as_string(conn), y_axis_title)

  def AddPointsExportedPanel(self):
    select_statement = textwrap.dedent("""
        SELECT
          $__timeGroupAlias(time, 1s),
          count(*)
        FROM gps
        WHERE
          $__timeFilter(time)
        GROUP BY 1
        ORDER BY 1
        """)
    self.AddGraphPanel(
        'GPS Points Exported Per Second', select_statement, 'points/s')


  def GenerateDashboard(self):
    return core.Dashboard(
        title=self.title,
        refresh='1s',
        time=core.Time('now-5m', 'now'),
        timePicker=core.TimePicker(
            refreshIntervals=[
                '1s',
                '3s',
                '10s',
                '30s',
            ],
            timeOptions=[
                '5m',
                '15m',
                '1h',
                '6h',
                '12h',
                '24h',
                '2d',
            ]
        ),
        panels=self.panels
    ).auto_panel_ids()
