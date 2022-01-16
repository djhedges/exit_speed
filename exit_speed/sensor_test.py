#!/usr/bin/python3
# Copyright 2022 Google LLC
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
"""Unitests for sensor.py"""
import time
import unittest

import mock
from absl.testing import absltest

from exit_speed import sensor

class TestAccelerometer(unittest.TestCase):
  """Accelerometer unittests."""

  def testSleepBasedOnHertz(self):
    now = time.time()
    cycle_time = now - 0.01
    with mock.patch.object(time, 'time') as mock_now:
      mock_now.return_value = now
      self.assertEqual(0.09,
          round(sensor.SleepBasedOnHertz(cycle_time, 10), 2))
      self.assertEqual(0.04,
          round(sensor.SleepBasedOnHertz(cycle_time, 20), 2))
      self.assertEqual(0.99,
          round(sensor.SleepBasedOnHertz(cycle_time, 1), 2))





if __name__ == '__main__':
  absltest.main()
