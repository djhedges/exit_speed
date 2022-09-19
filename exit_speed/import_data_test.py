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
"""Unitests for import_data.py"""
import os
import sys
import unittest

import fake_rpi
import gps
import mock
from absl import flags
from absl.testing import absltest

from exit_speed import postgres_test_lib
from exit_speed import tracks

# pylint: disable=wrong-import-position
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# Fixes dotstar import on Travis. import fake_rpi
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_dotstar
  from exit_speed import import_data
# pylint: enable=wrong-import-position


FLAGS = flags.FLAGS
FLAGS.set_default('config_path',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'testdata/test_postgres.yaml'))


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'testdata/')
EXPECTED_DURATIONS = {
    'Bug/Test Parking Lot/2020-06-11T22:00:00': {1: 31300000000,
                                                 2: 40230395520,
                                                 3: 41317467824,
                                                 4: 35329631376,
                                                 5: 40836133184,
    },
    'Bug/Test Parking Lot/2022-09-14T20:01:31.072481': {1: 171006277000,
                                                        2: 0},
    'Corrado/Portland International Raceway/2020-06-20': {1: 162400000000,
                                                          2: 96508634400,
                                                          3: 92020972432,
                                                          4: 92144408672,
                                                          5: 91838929920,
                                                          6: 90884317040,
                                                          7: 91417934496,
                                                          8: 91510285456,
                                                          9: 93499884352,
                                                          10: 92428355488,
                                                          11: 91658659808,
                                                          12: 91076583760,
                                                          13: 91270345664,
                                                          14: 90930683824,
                                                          15: 91508900336},
}


class TestPostgres(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Postgres unittests."""

  def setUp(self):
    super().setUp()
    self._AddMock(adafruit_dotstar, 'DotStar')
    self._AddMock(gps, 'gps')

  def testLoadProtos(self):
    data_dir = os.path.join(DATA_DIR,
                            'Bug/Test Parking Lot/2020-06-11T22:00:00')
    prefix_protos = import_data.LoadProtos(data_dir)
    self.assertEqual(1962, len(prefix_protos['GPSProcess']))

  def testCopyProtosToPostgres(self):
    data_dir = os.path.join(DATA_DIR,
                            'Bug/Test Parking Lot/2020-06-11T22:00:00')
    prefix_protos = import_data.LoadProtos(data_dir)
    import_data.CopyProtosToPostgres(prefix_protos)
    self.cursor.execute('SELECT count(*) FROM gps')
    self.assertEqual(1962, self.cursor.fetchone()[0])

  def testReRunMain(self):
    for test_dir, expected_durations in EXPECTED_DURATIONS.items():
      session = os.path.basename(test_dir)
      data_dir = os.path.join(DATA_DIR, test_dir)
      prefix_protos = import_data.LoadProtos(data_dir)
      import_data.ReRunMain(data_dir, prefix_protos['GPSProcess'])
      self.cursor.execute('SELECT * from sessions')
      db_id, _, track, car, live_data = self.cursor.fetchone()
      self.assertEqual(db_id, 1)
      self.assertEqual(track, tracks.test_track.TestTrack.name)
      self.assertEqual(car, 'Bug')
      self.assertFalse(live_data)
      self.cursor.execute(
          'SELECT id FROM sessions WHERE time = %s', (session,))
      session_id = self.cursor.fetchall()[0]
      self.cursor.execute(
          'SELECT number, duration_ns FROM laps '
          'WHERE session_id = %s '
          'AND duration_ns IS NOT NULL', (session_id,))
      for lap_number, duration_ns in self.cursor.fetchall():
        with self.subTest(
            name='Session %s Lap %d duration test' % (session, lap_number)):
          self.assertEqual(duration_ns, expected_durations.get(lap_number))


if __name__ == '__main__':
  absltest.main()
