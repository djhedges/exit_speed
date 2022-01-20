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
"""Grafana dashboard for live Honda data dashboard."""
import textwrap

from grafanalib.core import Dashboard
from grafanalib.core import Graph
from grafanalib.core import GridPos
from grafanalib.core import SqlTarget
from grafanalib.core import YAxes
from grafanalib.core import YAxis

dashboard = Dashboard(
    title='Honda Live',
    panels=[
        Graph(
            title='Speed',
            targets=[
                SqlTarget(
                    rawSql=textwrap.dedent("""
                    SELECT
                      points.time,
                      speed,
                      laps.number::text
                    FROM points
                    JOIN laps ON laps.id=points.lap_id
                    JOIN sessions ON laps.session_id=sessions.id
                    WHERE  $__timeFilter(points.time)
                    ORDER BY 1
                    """),
                    refId='A',
                ),
            ],
            yAxes=YAxes(
                YAxis(format='mph'),
            ),
            gridPos=GridPos(h=8, w=24, x=0, y=9),
        ),
    ],
).auto_panel_ids()
