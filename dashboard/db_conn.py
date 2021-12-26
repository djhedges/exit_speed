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
"""Database connection library."""

import logging
import os
import secret_manager
import sqlalchemy
from googleapiclient import discovery

# Local args used when running a development instance.
# {'password': '',
#  'username': '',
#  'database': 'exit-speed',
#  'drivername': 'postgresql+psycopg2',
#  'host': 'ip-address'}
SECRET_LOCAL_ID = (
    'projects/794720490237/secrets/db-conn-local-args/versions/latest')
# Obscuring the project id.  This is probably overkill but this code is public.
SECRET_PROJECT_ID = (
    'projects/794720490237/secrets/project_id/versions/latest')
INSTANCE_NAME = 'exit-speed'


def StartInstance():
  service = discovery.build('sqladmin', 'v1beta4')
  project = secret_manager.GetSecret(SECRET_PROJECT_ID)
  request = service.instances().get(project=project, instance=INSTANCE_NAME)
  response = request.execute()
  if response['settings']['activationPolicy'] == 'ALWAYS':
    logging.info('SQL instance is already up')
  else:
    request = service.instances().patch(
        project=project, instance=INSTANCE_NAME, body={
            'settings': {'activationPolicy': 'ALWAYS'}})
    response = request.execute()
    logging.info('Start SQL instance response: %s', response)



def InitPool():
  if os.getenv('GOOGLE_CLOUD_PROJECT'):
    StartInstance()
    local_args = secret_manager.GetSecret(SECRET_LOCAL_ID)
    return sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**local_args))
  return sqlalchemy.create_engine(sqlalchemy.engine.url.URL(
      **{'password': 'faster',
         'username': 'exit_speed',
         'database': 'exit_speed',
         'drivername': 'postgresql+psycopg2',
         'host': 'localhost'}))


POOL = InitPool()
