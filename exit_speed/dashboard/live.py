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
"""Live data dashboard."""
import datetime
import urllib
from typing import List
from typing import Text
from typing import Tuple

import dash
import plotly.express as px
from absl import app as absl_app
from absl import flags
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from exit_speed.dashboard import queries

FLAGS = flags.FLAGS
flags.DEFINE_bool(
    'debug', False,
    'Set to true to enable auto reloading of Python code at the expense of '
    'high CPU load.')

app = dash.Dash(__name__)
server = app.server

@app.callback(
  Output('url', 'href'),
  Input('url', 'href'),
  Input('time-window', 'value'),
  Input('points-dropdown', 'value'),
  Input('refresh', 'value'),
  prevent_initial_call=True,
)
def UpdateURL(href: Text, time_window: int, points: List[Text], refresh: int):
  args = {'time_window': time_window,
          'points': points,
          'refresh': refresh}
  return urllib.parse.urljoin(href, urllib.parse.urlencode(args, doseq=True))


@app.callback(
  Output('time-window', 'value'),
  Output('points-dropdown', 'value'),
  Output('refresh', 'value'),
  Input('url', 'pathname'),
)
def ParseURL(pathname: Text) -> Tuple[int, List[Text], int]:
  # Strip a leading "/" with [1:]
  params = urllib.parse.parse_qs(pathname[1:])
  if params.get('time_window'):
    time_window = int(params.get('time_window')[0])
  else:
    time_window = 1
  if params.get('refresh'):
    refresh = int(params.get('refresh')[0])
  else:
    refresh = 15
  points = params.get(
              'points',
              ['speed', 'rpm'])
  return time_window, points, refresh

@app.callback(
  Output('graphs', 'children'),
  Input('interval', 'n_intervals'),
  Input('time-window', 'value'),
  Input('points-dropdown', 'value'),
)
def UpdateGraph(
    unused_interval: int,
    time_window: int, point_values: List[Text]) -> List[dcc.Graph]:
  now = datetime.datetime.today()
  start_time = now - datetime.timedelta(minutes=time_window)
  if not isinstance(point_values, list):
    point_values = [point_values]
  graphs = []
  laps_data = queries.GetLiveData(start_time, point_values)
  for point_value in point_values:
    graph_type = 'graph'
    fig = px.line(
      laps_data,
      title=point_value,
      x='time',
      y=point_value,
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


@app.callback(
    Output('interval', 'interval'),
    Input('refresh', 'value'),
)
def SetIntervalRefresh(refresh: int) -> int:
  return refresh * 1000


def main(unused_argv):
  points_columns = queries.GetPointsColumns()

  app.layout = html.Div(
    style={'display': 'grid'},
    children=[
      dcc.Location(id='url', refresh=False),
      dcc.Interval(id='interval', interval=15 * 1000, n_intervals=-1),
      dcc.Link('Home', href='/'),
      dcc.Slider(
        id='time-window',
        min=1,
        max=60,
        step=5,
        tooltip={'placement': 'bottom', 'always_visible': True},
        marks={
            1:  {'label': '1m'},
            5:  {'label': '5m'},
            10: {'label': '10m'},
            15: {'label': '15m'},
            30: {'label': '30m'},
            60: {'label': '60m'},
        },
      ),
      dcc.Slider(
        id='refresh',
        min=3,
        max=60,
        value=3,
        step=5,
        tooltip={'placement': 'bottom', 'always_visible': True},
        marks={
            3:  {'label': '3s'},
            5:  {'label': '5s'},
            10: {'label': '10s'},
            15: {'label': '15s'},
            30: {'label': '30s'},
            60: {'label': '60s'},
        },
      ),
      dcc.Dropdown(
        id='points-dropdown',
        options=[{'label': i, 'value': i} for i in points_columns],
        clearable=False,
        multi=True,
      ),
      html.Div(id='graphs'),
    ],
  )
  app.run_server(host='0.0.0.0', debug=FLAGS.debug)


if __name__ == '__main__':
  absl_app.run(main)
