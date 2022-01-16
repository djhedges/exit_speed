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
"""Unitests for accelerometer.py"""
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
  from exit_speed import accelerometer
  import busio
  import adafruit_fxos8700
# pylint: enable=wrong-import-position


class TestAccelerometer(unittest.TestCase):
  """Accelerometer unittests."""

  def setUp(self):
    super().setUp()
    with mock.patch.object(busio, 'I2C'):
      with mock.patch.object(adafruit_fxos8700, 'FXOS8700'):
        self.accel = accelerometer.Accelerometer()

  def testCorrectValue(self):
    self.assertEqual(9.32704486216904,
        self.accel.CorrectValue('x', 9.924329799999999))
    self.assertEqual(10.836155704720122,
        self.accel.CorrectValue('y', 10.1596894))
    self.assertEqual(9.76962474276722,
        self.accel.CorrectValue('z', 10.260423308799998))

  def testGetGForces(self):
    self.accel.accelerometer.accelerometer = (
        0.3924229, -0.5072783912, 10.29870)
    result = self.accel.GetGForces()
    expected = (0.005457996517639941, -0.016599597585513083, 0.9997570415398239)
    self.assertEqual(expected, result)

  def testCalcPitchAndRoll(self):
    x_gs = 0.02
    y_gs = -0.71
    z_gs = 0.70
    pitch, roll = self.accel.CalcPitchAndRoll(x_gs, y_gs, z_gs)
    expected = (1.15, 45.41)
    self.assertEqual(expected, (round(pitch, 2), round(roll, 2)))

    x_gs = 0.72
    y_gs = -0.03
    z_gs = 0.69
    pitch, roll = self.accel.CalcPitchAndRoll(x_gs, y_gs, z_gs)
    expected = (46.19, 2.49)
    self.assertEqual(expected, (round(pitch, 2), round(roll, 2)))

  def testAccelerometerProcessLoop(self):
    self.accel.accelerometer.accelerometer = (
        0.3924229, -0.5072783912, 10.29870)
    with mock.patch.object(accelerometer, 'Accelerometer') as mock_accel:
      mock_accel.return_value = self.accel
      config = {'accelerometer': {'frequency_hz': 10}}
      point_queue = multiprocessing.Queue()
      proc = accelerometer.AccelerometerProcess(config, point_queue)
      while point_queue.empty():
        pass
      proc.Join()
      self.assertGreaterEqual(point_queue.qsize(), 0)


if __name__ == '__main__':
  absltest.main()
