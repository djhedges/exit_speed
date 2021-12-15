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

import db_conn
import dash
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
import pandas as pd
import textwrap

app = dash.Dash(__name__)
server = app.server

def GetSessions():
  select_statement = textwrap.dedent("""
  SELECT 
    track, 
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    sessions.id AS session_id, 
    laps.number AS lap_number,
    TO_CHAR((duration_ms || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    (count(points.time)::float / (duration_ms::float / 1000.0)) as points_per_second
  FROM laps
  JOIN points ON laps.id=points.lap_id
  JOIN sessions ON laps.session_id=sessions.id
  WHERE duration_ms IS NOT null
  GROUP BY sessions.id, track, sessions.time, laps.number, lap_time, laps.duration_ms
  """)
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)
  
df = GetSessions()
TRACKS = df['track'].unique()

app.layout = html.Div(
  children=[
    dcc.Dropdown(
      id='track-dropdown',
      options=[{'label': i, 'value': i} for i in TRACKS],
      value='Filter by track',
    ),
    dash_table.DataTable(
        id='sessions-table',
        columns=[
            {'name': i, 'id': i} for i in df.columns
            if 'id' not in i
        ],
        sort_action='native',
        sort_mode='single',
        sort_by=[{'column_id': 'lap_time',
                  'direction': 'asc'},
                 {'column_id': 'session_time',
                  'direction': 'desc'}],
        row_selectable='multi',
        page_action='native',
        page_current= 0,
        page_size= 10,
      ),
  ],
  style={'width': '50%'},
)


@app.callback(
  Output('sessions-table', 'data'),
  Input('track-dropdown', 'value'),
)
def UpdateSessions(track):
  filtered_df = df[df.track == track]
  return filtered_df.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
