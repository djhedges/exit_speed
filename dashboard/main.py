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
import pandas as pd

app = dash.Dash(__name__)
server = app.server

def GetSessions():
  select_statement = 'SELECT * FROM sessions ORDER BY time DESC'
  conn = db_conn.POOL.connect()
  return pd.io.sql.read_sql(select_statement, conn)
  
df = GetSessions()

app.layout = dash_table.DataTable(
    id='table',
    columns=[{'name': i, 'id': i} for i in df.columns],
    row_selectable='multi',
    data=df.to_dict('records'),
)

if __name__ == '__main__':
    app.run_server(debug=True)
