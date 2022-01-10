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
import os

import sqlalchemy

from exit_speed.dashboard import instance_manager
from exit_speed.dashboard import secret_manager

# Local args used when running a development instance.
# {'password': '',
#  'username': '',
#  'database': 'exit-speed',
#  'drivername': 'postgresql+psycopg2',
#  'host': 'ip-address'}
SECRET_LOCAL_ID = (
    'projects/794720490237/secrets/db-conn-local-args/versions/latest')


def InitPool() -> sqlalchemy.engine.base.Engine:
  if os.getenv('GOOGLE_CLOUD_PROJECT'):
    instance_manager.StartInstance()
    local_args = secret_manager.GetSecret(SECRET_LOCAL_ID)
    return sqlalchemy.create_engine(sqlalchemy.engine.url.URL(**local_args))
  return sqlalchemy.create_engine(sqlalchemy.engine.url.URL(
      **{'password': 'faster',
         'username': 'exit_speed',
         'database': 'exit_speed',
         'drivername': 'postgresql+psycopg2',
         'host': 'localhost'}))


POOL = InitPool()
