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

import dash
import queries
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

app = dash.Dash(__name__)
server = app.server
POINTS_COLUMNS = queries.GetPointsColumns()

app.layout = html.Div(
  style={'display': 'grid'},
  children=[
    dcc.Location(id='url', refresh=False),
    dcc.Link('Home', href='/'),
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
              ['speed'])
  return points


if __name__ == '__main__':
  app.run_server(debug=True)
