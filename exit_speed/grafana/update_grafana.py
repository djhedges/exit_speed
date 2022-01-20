#!/usr/bin/python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Updates the Grafana dashboards."""
import json
from typing import List
from typing import Text

import requests
from absl import app
from absl import flags
from grafanalib._gen import DashboardEncoder

from exit_speed.grafana import honda_live

FLAGS = flags.FLAGS
flags.DEFINE_string('api_key', None, 'Grafana API key')
flags.DEFINE_string('server', None, 'Grafana IP or hostname.')



def main(unused_argv: List[Text]):
  flags.mark_flag_as_required('api_key')
  flags.mark_flag_as_required('server')
  dash_json = json.dumps({'dashboard': honda_live.dashboard.to_json_data()},
                         sort_keys=True, indent=2, cls=DashboardEncoder)
  headers = {'Authorization': 'Bearer %s' % FLAGS.api_key,
             'Content-Type': 'application/json'}
  response = requests.post(
      'http://%s/api/dashboards/db' % FLAGS.server,
      data=dash_json,
      headers=headers)
  print(response)


if __name__ == '__main__':
  app.run(main)
