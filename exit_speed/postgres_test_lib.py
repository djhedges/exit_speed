#!/usr/bin/python3
# Copyright 2020 Google LLC
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
"""Test instance of the Postgres database."""

import datetime
import psycopg2
import mock
import os
import pytz
import unittest
import testing.postgresql
from absl.testing import absltest

from exit_speed import exit_speed_pb2
from exit_speed import postgres


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
  Postgresql.clear_cache()


class PostgresTestBase(unittest.TestCase):
  """Loads the exit_speed schema and mocks out database connections."""

  def setUp(self):
    self.postgresql = Postgresql()
    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'postgres_schema.sql')
    with open(schema_path) as schema_file:
      statements = ''.join(schema_file.readlines())
    self.conn = psycopg2.connect(**self.postgresql.dsn())
    self.cursor = self.conn.cursor()
    self.cursor.execute(statements)
    self.conn.commit()
    mock_connect = self._AddMock(postgres, 'ConnectToDB')
    def _Connect():
      return psycopg2.connect(**self.postgresql.dsn())
    mock_connect.side_effect = _Connect

  def _AddMock(self, module, name):
    patch = mock.patch.object(module, name)
    self.addCleanup(patch.stop)
    return patch.start()

  def tearDown(self):
    self.cursor.close()
    self.conn.close()
    self.postgresql.stop()
