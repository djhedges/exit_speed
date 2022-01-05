# Copyright 2022 Google LLC
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

import live
from app import app
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output


BASE_HTML = html.Div([
  dcc.Location(id='url', refresh=False),
  dcc.Link('Home', href='/'),
  html.Br(),
  dcc.Link('Live Data', href='/live/'),
  html.Br(),
  html.Div(id='page-content')
])

app.layout = BASE_HTML
app.validation_layout = html.Div([
    BASE_HTML,
    live.LAYOUT,
])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def URLRouting(pathname):
  if pathname == '/live/':
    return live.LAYOUT


@app.callback(
  Output('url', 'href'),
  Input('url', 'href'),
  Input('points-dropdown', 'value'),
  prevent_initial_call=True,
)
def UpdateURL(href, points):
  args = {'points': points}
  return urllib.parse.urljoin(href, urllib.parse.urlencode(args, doseq=True))


@app.callback(
  Output('points-dropdown', 'value'),
  Input('url', 'pathname'),
)
def ParseURL(pathname):
  # Strip a leading "/" with [1:]
  params = urllib.parse.parse_qs(pathname[1:])
  points = params.get(
              'points',
              [
               'speed',
               'tps_voltage',
               'front_brake_pressure_percentage',
               ])
  return points


if __name__ == '__main__':
  app.run_server(debug=True)
