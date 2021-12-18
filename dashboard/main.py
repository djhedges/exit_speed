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
from dash.dependencies import ALL
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import Output
import flask
import pandas as pd
import plotly.express as px
import urllib
import textwrap

app = dash.Dash(__name__)
server = app.server


def GetSessions():
  select_statement = textwrap.dedent("""
  SELECT 
    TO_CHAR((duration_ms || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.id as lap_id,
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
  df['front_brake_pressure_percentage'] = (
    df['front_brake_pressure_voltage'] / df['front_brake_pressure_voltage'].max())
  df['rear_brake_pressure_percentage'] = (
    df['rear_brake_pressure_voltage'] / df['rear_brake_pressure_voltage'].max())
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
  columns.extend(['front_brake_pressure_percentage', 'rear_brake_pressure_percentage'])
  return columns
  
df = GetSessions()
TRACKS = df['track'].unique()
POINTS_COLUMNS = GetPointsColumns()


app.layout = html.Div(
  style={'display': 'grid'},
  children=[
    dcc.Store(id='memory'),
    dcc.Location(id='url', refresh=False),
    dcc.Dropdown(
      id='track-dropdown',
      options=[{'label': i, 'value': i} for i in TRACKS],
      searchable=False,
      clearable=False,
      style={'width': '50%'},
    ),
    dcc.Dropdown(
      id='points-dropdown',
      options=[{'label': i, 'value': i} for i in POINTS_COLUMNS],
      clearable=False,
      multi=True,
    ),
    dash_table.DataTable(
        id='sessions-table',
        columns=[
            {'name': i, 'id': i} for i in df.columns
        ],
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        sort_by=[{'column_id': 'lap_time',
                  'direction': 'asc'},
                 {'column_id': 'session_time',
                  'direction': 'desc'}],
        row_selectable='multi',
        page_action='native',
        page_current= 0,
        page_size= 10,
      ),
    html.Div(id='graphs'),
  ], 
)

def _GetLapIds(selected_rows):
  lap_ids = []
  for selected_row in selected_rows:
    row = df.iloc[selected_row]
    lap_ids.append(row['lap_id'])
  return lap_ids

@app.callback(
  Output('url', 'href'),
  Input('url', 'href'),
  Input('track-dropdown', 'value'),
  Input('sessions-table', 'selected_rows'),
  Input('points-dropdown', 'value'),
  prevent_initial_call=True,
)
def UpdateURL(href, track, selected_rows, points):
  args = {'track': track,
          'points': points}
  if selected_rows:
    args['lap_ids'] = _GetLapIds(selected_rows)
  return urllib.parse.urljoin(href, urllib.parse.urlencode(args, doseq=True))


@app.callback(
  Output('track-dropdown', 'value'),
  Output('points-dropdown', 'value'),
  Output('sessions-table', 'selected_rows'),
  Input('url', 'pathname'),
)
def ParseURL(pathname):
  # Strip a leading "/" with [1:]
  params = urllib.parse.parse_qs(pathname[1:])
  url_track = params.get('track')
  if url_track:
    track = url_track[0]
  else:
    track = TRACKS[0]
  points = params.get(
              'points',  
              ['speed', 'tps_voltage', 'front_brake_pressure_percentage'])
  session_row_indexes = []
  for lap_id in params.get('lap_ids', []):
    lap_id = int(lap_id)
    session_row_index = df.index[df['lap_id'] == lap_id].tolist()[0]
    session_row_indexes.append(session_row_index)
  return track, points, session_row_indexes


@app.callback(
  Output('sessions-table', 'data'),
  Input('track-dropdown', 'value'),
)
def UpdateSessions(track):
  filtered_df = df[df.track == track]
  return filtered_df.to_dict('records')


@app.callback(
  Output('graphs', 'children'),
  Input('sessions-table', 'selected_rows'),
  Input('points-dropdown', 'value'),
)
def UpdateGraph(selected_rows, point_values):
  if not isinstance(point_values, list):
    point_values = [point_values]
  if selected_rows:
    graphs = []
    lap_ids = _GetLapIds(selected_rows)
    for point_value in point_values:
      lap_data = GetSingleLapData(lap_ids)
      fig = px.line(
        lap_data, x='elapsed_distance_m', 
        y=point_value, 
        color='lap_id', 
        hover_data=['lap_id', 'lap_number', point_value])
      fig.update_xaxes(showspikes=True)
      fig.update_layout(hovermode="x unified")
      graph = dcc.Graph({'type': 'graph', 
                         'index': point_values.index(point_value)},
                        figure=fig,
                        style={'display': 'inline-grid', 'width': '50%'})
      graphs.append(graph)
    return graphs
  # Empty line when no rows have been selected.
  return [dcc.Graph(figure=px.line())]


@app.callback(
    Output({'type': 'graph', 'index': ALL}, 'relayoutData'),
    Output({'type': 'graph', 'index': ALL}, 'figure'),
    Input({'type': 'graph', 'index': ALL}, 'relayoutData'),
    State({'type': 'graph', 'index': ALL}, 'figure'))
def LinkedZoom(relayout_data, figure_states):
    unique_data = None
    for data in relayout_data:
      if relayout_data.count(data) == 1:
        unique_data = data
    if unique_data:
      for figure_state in figure_states:
        if unique_data.get('xaxis.autorange'):
          figure_state['layout']['xaxis']['autorange'] = True
        else:
          figure_state['layout']['xaxis']['range'] = [
              unique_data['xaxis.range[0]'], unique_data['xaxis.range[1]']]
          figure_state['layout']['xaxis']['autorange'] = False
      return [unique_data] * len(relayout_data), figure_states
    return relayout_data, figure_states


if __name__ == '__main__':
    app.run_server(debug=True)
