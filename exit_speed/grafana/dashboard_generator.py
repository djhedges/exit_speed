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

from exit_speed import timescale


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
                    ORDER BY 1
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

  def AddPointPanel(
      self, title: Text, point_values: Tuple[Text], y_axis_title: Text):
    select_statement = textwrap.dedent("""
        SELECT
          points.time,
          {columns},
          laps.number::text
        FROM points
        JOIN laps ON laps.id=points.lap_id
        JOIN sessions ON laps.session_id=sessions.id
        WHERE  $__timeFilter(points.time)
        ORDER BY 1
        """)
    query = sql.SQL(select_statement).format(columns=sql.SQL(',').join(
            [sql.Identifier(col) for col in point_values]))
    with timescale.ConnectToDB() as conn:
      raw_string = query.as_string(conn)
    self.AddPanel(
        core.Graph(
            title=title,
            targets=[
                core.SqlTarget(
                    rawSql=raw_string,
                    format=core.TABLE_TARGET_FORMAT,
                ),
            ],
            yAxes=core.YAxes(
                core.YAxis(format=y_axis_title),
            ),
        )
    )

  def GenerateDashboard(self):
    return core.Dashboard(
        title=self.title,
        refresh=False,
        time=core.Time('now-2m', 'now'),
        panels=self.panels
    ).auto_panel_ids()
