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
"""Unitests for gyroscope.py"""
import multiprocessing
import sys
import unittest

import fake_rpi
import mock
from absl.testing import absltest
# pylint: disable=wrong-import-position
# Fixes dotstar import on Travis.
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_fxas21002c
  import busio
  from exit_speed import gyroscope
# pylint: enable=wrong-import-position


class TestGyroscope(unittest.TestCase):
  """Gyroscope unittests."""

  def setUp(self):
    super().setUp()
    with mock.patch.object(busio, 'I2C'):
      with mock.patch.object(adafruit_fxas21002c, 'FXAS21002C'):
        self.gyroscope = gyroscope.Gyroscope()

  def testGetRotationalValues(self):
    self.gyroscope.sensor.gyroscope = (
        0.024816400301794373, -0.27052603405912107, -0.9467047653591117)
    expected = (1.421875, -15.5, -54.2421875)
    self.assertTupleEqual(expected, self.gyroscope.GetRotationalValues())

  def testGryoscopeProcessLoop(self):
    self.gyroscope.sensor.gyroscope = (
        0.024816400301794373, -0.27052603405912107, -0.9467047653591117)
    with mock.patch.object(gyroscope, 'Gyroscope') as mock_gyro:
      mock_gyro.return_value = self.gyroscope
      config = {'gyroscope': {'frequency_hz': 10}}
      point_queue = multiprocessing.Queue()
      proc = gyroscope.GyroscopeProcess(config, point_queue)
      while point_queue.empty():
        pass
      proc.Join()
      self.assertGreaterEqual(point_queue.qsize(), 0)


if __name__ == '__main__':
  absltest.main()
