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

import mock
import unittest
from absl.testing import absltest
import tire_temperature
from mlx import mlx90640

def _CreateRawFrame():
  frame = []
  for _ in range(32 * 24):
    frame.append(30.0)
  return frame


class TestInfraRedSensor(unittest.TestCase):
  """Gyroscope unittests."""

  def setUp(self):
    super().setUp()
    patch = mock.patch.object(mlx90640, 'Mlx9064x')
    self.addCleanup(patch.stop)
    self.mock_mlx = patch.start()
    self.sensor = tire_temperature.InfraRedSensor()

  def testReadFrame(self):
    self.mock_mlx.read_frame.return_value = _CreateRawFrame()
    self.sensor.ReadFrame()

  def testFormatFrame(self):
    raw_frame = _CreateRawFrame()
    formatted_frame = self.sensor.FormatFrame(raw_frame)
    row_count = 0
    for row in formatted_frame:
      row_count += 1
      self.assertEqual(32, len(row))
    self.assertEqual(24, row_count)

if __name__ == '__main__':
  absltest.main()
