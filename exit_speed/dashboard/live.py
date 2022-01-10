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

import dash
import plotly.express as px
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

from exit_speed.dashboard import queries

app = dash.Dash(__name__)
server = app.server
POINTS_COLUMNS = queries.GetPointsColumns()

app.layout = html.Div(
  style={'display': 'grid'},
  children=[
    dcc.Location(id='url', refresh=False),
    dcc.Link('Home', href='/'),
    dcc.Slider(
      id='time-slider',
      min=5,
      max=60,
      step=5,
      value=15,
      tooltip={'placement': 'bottom', 'always_visible': True},
      marks={
          5:  {'label': '5m'},
          10: {'label': '10m'},
          15: {'label': '15m'},
          30: {'label': '30m'},
          60: {'label': '60m'},
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
  Input('points-dropdown', 'value'),
  prevent_initial_call=True,
)
def UpdateURL(href: Text, points: List[Text]):
  args = {'points': points}
  return urllib.parse.urljoin(href, urllib.parse.urlencode(args, doseq=True))


@app.callback(
  Output('points-dropdown', 'value'),
  Input('url', 'pathname'),
)
def ParseURL(pathname: Text) -> List[Text]:
  # Strip a leading "/" with [1:]
  params = urllib.parse.parse_qs(pathname[1:])
  points = params.get(
              'points',
              ['speed', 'accelerometer_z'])
  return points


@app.callback(
  Output('graphs', 'children'),
  Input('time-slider', 'value'),  # lap_ids
  Input('points-dropdown', 'value'),
)
def UpdateGraph(time_slider: int, point_values: List[Text]) -> List[dcc.Graph]:
  now = datetime.datetime.today()
  start_time = now - datetime.timedelta(minutes=time_slider)
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
      color='lap_number',
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


if __name__ == '__main__':
  app.run_server(debug=True)
