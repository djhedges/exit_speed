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
"""App Engine dashboard using Dash, Plotly and Pandas."""

import db_conn
import dash
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import ALL
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import Output
import pandas as pd
import plotly.express as px
import queries
import urllib

app = dash.Dash(__name__)
server = app.server
df = queries.GetSessions()
POINTS_COLUMNS = queries.GetPointsColumns()
TRACKS = queries.GetTracks()


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

@app.callback(
  Output('url', 'href'),
  Input('url', 'href'),
  Input('track-dropdown', 'value'),
  Input('sessions-table', 'selected_row_ids'),  # lap_ids
  Input('points-dropdown', 'value'),
  prevent_initial_call=True,
)
def UpdateURL(href, track, lap_ids, points):
  args = {'track': track,
          'points': points}
  if lap_ids:
    args['lap_ids'] = lap_ids
  return urllib.parse.urljoin(href, urllib.parse.urlencode(args, doseq=True))


@app.callback(
  Output('track-dropdown', 'value'),
  Output('points-dropdown', 'value'),
  Output('sessions-table', 'selected_row_ids'),
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
              ['racing_line',
               'speed',
               'tps_voltage',
               'front_brake_pressure_percentage',
               'gsum'])
  lap_ids = [int(lap_id) for lap_id in params.get('lap_ids', [])]
  return track, points, lap_ids


@app.callback(
  Output('sessions-table', 'data'),
  Input('track-dropdown', 'value'),
)
def UpdateSessions(track):
  filtered_df = df[df.track == track]
  return filtered_df.to_dict('records')


@app.callback(
  Output('graphs', 'children'),
  Input('sessions-table', 'selected_row_ids'),  # lap_ids
  Input('points-dropdown', 'value'),
)
def UpdateGraph(lap_ids, point_values):
  if not isinstance(point_values, list):
    point_values = [point_values]
  if lap_ids:
    graphs = []
    laps_data = queries.GetLapsData(lap_ids)
    for point_value in point_values:
      if point_value == 'racing_line':
        graph_type = 'map'
        fig = px.line_geo(
            laps_data,
            title=point_value,
            lat='lat',
            lon='lon',
            color='lap_id',
            fitbounds='locations',
            )
      else:
        graph_type = 'graph'
        fig = px.line(
          laps_data,
          title=point_value,
          x='elapsed_distance_m',
          y=point_value,
          color='lap_id',
          hover_data=['lap_id', 'lap_number', point_value])
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(fixedrange=True)
        fig.update_layout(hovermode='x unified')
      graph = dcc.Graph({'type': graph_type,
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
