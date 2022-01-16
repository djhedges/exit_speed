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
"""Unitests for replay_data.py"""
import os
import sys
import unittest

import fake_rpi
import gps
import mock
import psycopg2
import testing.postgresql
from absl import flags
from absl.testing import absltest

from exit_speed import timescale
# pylint: disable=wrong-import-position
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# Fixes dotstar import on Travis. import fake_rpi
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_dotstar
  from exit_speed import replay_data
# pylint: enable=wrong-import-position

FLAGS = flags.FLAGS
FLAGS.set_default('config_path',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
    'testdata/test_config.yaml'))
FLAGS.set_default('data_log_path', '/tmp')
FLAGS.set_default('filepath', '/dev/null')

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
  Postgresql.clear_cache()


class TestReplayData(unittest.TestCase):
  """More of a end-to-end test for data in testdata/."""

  def setUp(self):
    super().setUp()
    self._AddMock(adafruit_dotstar, 'DotStar')
    self._AddMock(gps, 'gps')
    self.postgresql = Postgresql()
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'testdata/timescale_schema')) as schema_file:
      statements = ''.join(schema_file.readlines())
    self.conn = psycopg2.connect(**self.postgresql.dsn())
    self.cursor = self.conn.cursor()
    self.cursor.execute(statements)
    self.conn.commit()
    mock_connect = self._AddMock(timescale, 'ConnectToDB')
    def _Connect():
      return psycopg2.connect(**self.postgresql.dsn())
    mock_connect.side_effect = _Connect

  def _AddMock(self, module, name):
    patch = mock.patch.object(module, name)
    self.addCleanup(patch.stop)
    return patch.start()

  def testEndToEnd(self):
    test_data_file = os.path.join(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
            'testdata/test_parking_lot_20hz_2020-06-11T22_1.data'))
    if test_data_file.endswith('.data'):
      with self.subTest(name=test_data_file):
        es = replay_data.ReplayLog(test_data_file)
        point_count = 0
        for lap in es.session.laps:
          point_count += len(lap.points)
        self.cursor.execute('SELECT count(*) FROM points')
        self.assertEqual(point_count, self.cursor.fetchone()[0])


if __name__ == '__main__':
  absltest.main()
