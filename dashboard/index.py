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
import live
from app import app
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output

app.layout = html.Div([
  dcc.Location(id='url', refresh=False),
  dcc.Link('Home', href='/'),
  html.Br(),
  dcc.Link('Live Data', href='/live/'),
  html.Br(),
  html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def URLRouting(pathname):
  print(pathname)
  if pathname == '/live/':
    return live.LAYOUT


if __name__ == '__main__':
  app.run_server(debug=True)
