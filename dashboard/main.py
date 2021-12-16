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
import plotly.express as px
import textwrap

app = dash.Dash(__name__)
server = app.server



def GetSessions():
  select_statement = textwrap.dedent("""
  SELECT 
    track, 
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.id as lap_id,
    laps.number AS lap_number,
    TO_CHAR((duration_ms || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    (count(points.time)::float / (duration_ms::float / 1000.0)) as points_per_second
  FROM laps
  JOIN points ON laps.id=points.lap_id
  JOIN sessions ON laps.session_id=sessions.id
  WHERE duration_ms IS NOT null
  GROUP BY sessions.id, track, sessions.time, laps.id, laps.number, lap_time, laps.duration_ms
  """)
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)


def GetSingleLapData(lap_ids):
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
  return [row[0] for row in resp.fetchall()]
  
df = GetSessions()
TRACKS = df['track'].unique()
POINTS_COLUMNS = GetPointsColumns()


app.layout = html.Div(
  children=[
    dcc.Dropdown(
      id='track-dropdown',
      options=[{'label': i, 'value': i} for i in TRACKS],
      value=TRACKS[0],
      searchable=False,
      clearable=False,
    ),
    dcc.Dropdown(
      id='points-dropdown',
      options=[{'label': i, 'value': i} for i in POINTS_COLUMNS],
      value='speed',
      clearable=False,
    ),
    dash_table.DataTable(
        id='sessions-table',
        columns=[
            {'name': i, 'id': i} for i in df.columns
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
    dcc.Graph(id='lap-graph'),
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


@app.callback(
  Output('lap-graph', 'figure'),
  Input('sessions-table', 'selected_rows'),
  Input('points-dropdown', 'value'),
)
def UpdateGraph(selected_rows, point_value):
  if selected_rows:
    lap_ids = []
    for selected_row in selected_rows:
      row = df.iloc[selected_row]
      lap_ids.append(row['lap_id'])
    lap_data = GetSingleLapData(lap_ids)
    fig = px.line(lap_data, x='elapsed_distance_m', y=point_value, color='lap_id', hover_data=['lap_id', 'lap_number', point_value])
    fig.update_xaxes(showspikes=True)
    fig.update_layout(hovermode="x unified")
    return fig
  return px.line()  # Empty line when no rows have been selected.


if __name__ == '__main__':
    app.run_server(debug=True)
