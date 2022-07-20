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
"""Unitests for postgres.py"""

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


class TestPostgres(unittest.TestCase):
  """Postgres unittests."""

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

  def testArgsMapLookup(self):
    self.assertTupleEqual(
            postgres.ARGS_GPS,
            postgres.ARGS_MAP[exit_speed_pb2.Gps])

  def testPrepareMapLookup(self):
    self.assertEqual(
            postgres.PREPARE_GPS,
            postgres.PREPARE_MAP[exit_speed_pb2.Gps])

  def testInsertMapLookup(self):
    self.assertEqual(
            postgres.INSERT_GPS,
            postgres.INSERT_MAP[exit_speed_pb2.Gps])

  def testExportGps(self):
    proto = exit_speed_pb2.Gps(
      lat=23,
      lon=34,
      alt=45,
      speed_ms=86)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Gps, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM gps')
    time, lat, lon, alt, speed_ms = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(23, lat)
    self.assertEqual(34, lon)
    self.assertEqual(45, alt)
    self.assertEqual(86, speed_ms)

  def testExportAccelerometer(self):
    proto = exit_speed_pb2.Accelerometer(
      accelerometer_x = 1.0,
      accelerometer_y = 2.0,
      accelerometer_z = 3.0)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Accelerometer, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM accelerometer')
    time, accelerometer_x, accelerometer_y, accelerometer_z = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(1.0, accelerometer_x)
    self.assertEqual(2.0, accelerometer_y)
    self.assertEqual(3.0, accelerometer_z)


if __name__ == '__main__':
  absltest.main()
