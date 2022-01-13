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
"""App Engine dashboard using Dash, Plotly and Pandas."""
import urllib
from typing import Dict
from typing import List
from typing import Text
from typing import Tuple

import dash
import pandas as pd
import plotly.express as px
from absl import app as absl_app
from absl import flags
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import ALL
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from exit_speed.dashboard import queries

FLAGS = flags.FLAGS
flags.DEFINE_bool(
    'debug', True,
    'Set to true to enable auto reloading of Python code at the expense of '
    'high CPU load.')

app = dash.Dash(__name__)
server = app.server
SESSIONS = queries.GetSessions()
POINTS_COLUMNS = queries.GetPointsColumns() + [
    'front_brake_pressure_percentage',
    'rear_brake_pressure_percentage',
    'racing_line',
    'gsum',
    'time_delta'
    ]
TRACKS = queries.GetTracks()


app.layout = html.Div(
  style={'display': 'grid'},
  children=[
    dcc.Location(id='url', refresh=False),
    dcc.Link('Home', href='/'),
    dcc.Link('Clear', href='/track=None&points=None'),
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
            {'name': i, 'id': i} for i in SESSIONS.columns
        ],
        filter_action='native',
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
def UpdateURL(
    href: Text,
    track: Text,
    lap_ids: List[int],
    points: List[Text],
  ) -> Text:
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
def ParseURL(pathname: Text) -> Tuple[Text, List[Text], List[int]]:
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
               'time_delta',
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
def UpdateSessions(track: pd.DataFrame) -> pd.DataFrame:
  filtered_df = SESSIONS[SESSIONS.track == track]
  return filtered_df.to_dict('records')


@app.callback(
  Output('graphs', 'children'),
  Input('sessions-table', 'selected_row_ids'),  # lap_ids
  Input('points-dropdown', 'value'),
)
def UpdateGraph(
    lap_ids: List[int], point_values: List[Text]) -> List[dcc.Graph]:
  if not isinstance(point_values, list):
    point_values = [point_values]
  if lap_ids:
    graphs = []
    laps_data = queries.GetLapsData(lap_ids, point_values)
    for point_value in point_values:
      figure_data = laps_data
      title = point_value
      # Copied so that time_delta can redefine without breaking other graphs.
      if point_value == 'time_delta':
        figure_data = laps_data.copy()
      if point_value == 'racing_line':
        graph_type = 'map'
        fig = px.line_geo(
            laps_data,
            title=title,
            lat='lat',
            lon='lon',
            color='lap_id',
            fitbounds='locations',
            )
      else:
        if point_value == 'time_delta':
          if len(lap_ids) < 2:
            continue  # Need at least two laps to make a comparison.
          figure_data = queries.GetTimeDelta(lap_ids)
          title = 'time_delta vs first selected lap (lap_id: %s)' % lap_ids[0]
        graph_type = 'graph'
        fig = px.line(
          figure_data,
          title=title,
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
def LinkedZoom(
    relayout_data: List[Dict],
    figure_states: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
  unique_data = None
  for data in relayout_data:
    if relayout_data.count(data) == 1:
      unique_data = data
  if unique_data:
    for figure_state in figure_states:
      if unique_data.get('xaxis.autorange'):
        figure_state['layout']['xaxis']['autorange'] = True
      if unique_data.get('xaxis.range[0]'):
        figure_state['layout']['xaxis']['range'] = [
            unique_data['xaxis.range[0]'], unique_data['xaxis.range[1]']]
        figure_state['layout']['xaxis']['autorange'] = False
    return [unique_data] * len(relayout_data), figure_states
  return relayout_data, figure_states


def main(unused_argv):
  app.run_server(debug=FLAGS.debug)


if __name__ == '__main__':
  absl_app.run(main)
