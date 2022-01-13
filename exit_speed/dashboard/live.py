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
import json
import urllib
from typing import Dict
from typing import List
from typing import Text
from typing import Tuple

import dash
import dateutil
import pandas as pd
import plotly.express as px
from absl import app as absl_app
from absl import flags
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import MATCH
from dash.dependencies import Output

from exit_speed.dashboard import queries

FLAGS = flags.FLAGS
flags.DEFINE_bool(
    'debug', True,
    'Set to true to enable auto reloading of Python code at the expense of '
    'high CPU load.')

app = dash.Dash(__name__)
server = app.server
POINTS_COLUMNS = queries.GetPointsColumns()

app.layout = html.Div(
  style={'display': 'grid'},
  children=[
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='max-time'),
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
      options=[{'label': i, 'value': i} for i in POINTS_COLUMNS],
      clearable=False,
      multi=True,
    ),
    html.Div(id='graphs'),
  ],
)

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
    time_window = 15
  if params.get('refresh'):
    refresh = int(params.get('refresh')[0])
  else:
    refresh = 3
  points = params.get(
              'points',
              ['speed', 'rpm'])
  return time_window, points, refresh


def _GetMaxTime(laps_data: pd.DataFrame) -> Text:
  max_time = laps_data['time'].max().to_pydatetime()
  return json.dumps(max_time.isoformat())


@app.callback(
  Output('graphs', 'children'),
  Output('max-time', 'data'),
  Input('time-window', 'value'),
  Input('points-dropdown', 'value'),
)
def UpdateGraph(
    time_window: int, point_values: List[Text]) -> Tuple[List[dcc.Graph], str]:
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
  return graphs, _GetMaxTime(laps_data)


@app.callback(
    Output('interval', 'interval'),
    Input('refresh', 'value'),
)
def SetIntervalRefresh(refresh: int) -> int:
  return refresh * 1000


@app.callback(
  Output({'type': 'graph', 'index': MATCH}, 'extendData'),
  Input({'type': 'graph', 'index': MATCH}, 'id'),
  Input('points-dropdown', 'value'),
  Input('max-time', 'data'),
  Input('interval', 'n_intervals'),
  Input('refresh', 'value'),
  prevent_initial_call=True,
)
def ExtendGraphData(
    graph_id: Dict,
    point_values: List[Text],
    max_time: str,
    n_interval: int,
    refresh: int):
  if n_interval:
    if not isinstance(point_values, list):
      point_values = [point_values]
    max_time = dateutil.parser.parse(json.loads(max_time))
    start_time = max_time + datetime.timedelta(
        seconds=n_interval * refresh)
    point_value = point_values[graph_id['index']]
    lap_data = queries.GetLiveData(start_time, [point_value])
    x_data = lap_data['time'].astype(str).values
    y_data = lap_data[point_value].values
    # Hover data.
    customdata = lap_data[['lap_id', 'lap_number']].values
    return {'updateData': {'x': [x_data],
                           'y': [y_data],
                           'customdata': [customdata]},
            'traceIndices': [0],
            # Makes the assumption data was logged at 10hz.
            'maxPoints': 10 * 60 * refresh}


def main(unused_argv):
  app.run_server(debug=FLAGS.debug)


if __name__ == '__main__':
  absl_app.run(main)
