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

import mock
import unittest
from absl.testing import absltest
import accelerometer
import busio
import adafruit_adxl34x


class TestAccelerometer(unittest.TestCase):
  """Accelerometer unittests."""

  def setUp(self):
    super().setUp()
    with mock.patch.object(busio, 'I2C'):
      with mock.patch.object(adafruit_adxl34x, 'ADXL345'):
        self.accel = accelerometer.Accelerometer()

  def testCorrectValue(self):
    res = self.accel.CorrectValue('x', 9.924329799999999)
    self.assertEqual(1, int(res / self.accel.GRAVITY))
    res = self.accel.CorrectValue('y', 10.1596894)
    self.assertEqual(1, int(res / self.accel.GRAVITY))
    res = self.accel.CorrectValue('z', 10.9049948)
    self.assertEqual(1, int(res / self.accel.GRAVITY))

  def testGetGForces(self):
    self.accel.accelerometer.acceleration = (9.7674234, 10.0812362, 10.8657682)
    result = self.accel.GetGForces()
    expected = (1.0, 1.0, 1.0)
    self.assertEqual(expected, result)

if __name__ == '__main__':
  absltest.main()