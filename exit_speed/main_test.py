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
"""ExitSpeed unittest."""
import datetime
import gps
import os
import sys
import unittest

import fake_rpi
import mock
from absl import flags
from absl.testing import absltest

from exit_speed import common_lib
from exit_speed import exit_speed_pb2
from exit_speed import postgres_test_lib
from exit_speed import tracks
# pylint: disable=wrong-import-position
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# Fixes adafruit_adxl34x import on Travis.
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_dotstar
  from exit_speed import main
# pylint: enable=wrong-import-position

FLAGS = flags.FLAGS
FLAGS.set_default('config_path',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'testdata/test_config.yaml'))


class TestExitSpeed(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """ExitSpeed unittest."""

  def setUp(self):
    super().setUp()
    self._AddMock(adafruit_dotstar, 'DotStar')
    self._AddMock(gps, 'gps')

  def _AddMock(self, module, name):
    patch = mock.patch.object(module, name)
    self.addCleanup(patch.stop)
    return patch.start()

  def testProcessPoint(self):
    es = main.ExitSpeed()
    point = exit_speed_pb2.Gps()
    point.lat = 12.000001
    point.lon = 23.000002
    point.time.FromJsonString(u'2020-05-23T17:47:44.200Z')
    es.point = point
    es.ProcessPoint()

  def testSetLapTime(self):
    es = main.ExitSpeed()
    first_point = exit_speed_pb2.Gps()
    first_point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    last_point = exit_speed_pb2.Gps()
    last_point.time.FromJsonString(u'2020-05-23T17:49:00.100Z')
    lap = []
    lap.append(first_point)
    lap.append(last_point)
    es.current_lap = lap
    es.laps = {1: lap}
    es.session = common_lib.Session(
      time=datetime.datetime.today(),
      track=tracks.portland_internal_raceways.PortlandInternationalRaceway,
      car='RC Car',
      live_data=False)
    es.SetLapTime()
    self.assertEqual(76 * 1e9, es.leds.best_lap_duration_ns)
    self.assertEqual(es.leds.best_lap, lap)

  def testCrossStartFinish(self):
    point_a = exit_speed_pb2.Gps()
    point_b = exit_speed_pb2.Gps()
    point_c = exit_speed_pb2.Gps()
    point_a.time.FromMilliseconds(1000)
    point_b.time.FromMilliseconds(2000)
    point_c.time.FromMilliseconds(3000)
    point_a.lat = 45.594961
    point_a.lon = -122.694508
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    lap = []
    lap.extend([point_a, point_b])
    es = main.ExitSpeed(min_points_per_session=0)
    es.current_lap = lap
    es.lap_number = 1
    es.laps = {1: lap}
    es.track = tracks.portland_internal_raceways.PortlandInternationalRaceway
    es.point = point_c
    es.session = common_lib.Session(
      time=datetime.datetime.today(),
      track=tracks.portland_internal_raceways.PortlandInternationalRaceway,
      car='RC Car',
      live_data=False)
    es.CrossStartFinish()
    self.assertEqual(2, es.lap_number)
    self.assertEqual(2, len(es.laps))
    self.assertEqual(2, len(es.laps[1]))
    self.assertEqual(2, len(es.laps[2]))
    self.assertIn(point_a, es.laps[1])
    self.assertIn(point_b, es.laps[1])
    self.assertIn(point_b, es.laps[2])
    self.assertIn(point_c, es.laps[2])
    self.assertNotIn(point_c, es.laps[1])

  def testProcessLap(self):
    es = main.ExitSpeed()
    es.AddNewLap()
    es.point = exit_speed_pb2.Gps()
    es.ProcessLap()
    self.assertTrue(es.current_lap)


if __name__ == '__main__':
  absltest.main()
