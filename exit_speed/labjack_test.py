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
"""Unitests for Labjack."""
import multiprocessing
import os
import unittest

import mock
import u3
from absl.testing import absltest

from exit_speed import config_lib
from exit_speed import gps_pb2
from exit_speed import labjack


class TestLabjack(unittest.TestCase):
  """Unitests for Labjack."""

  def setUp(self):
    super().setUp()
    config = config_lib.LoadConfig(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
            'testdata/test_labjack_config.yaml'))
    self.point_queue = multiprocessing.Queue()
    self.labjack = labjack.Labjack(
        config, self.point_queue, start_process=False)
    self.mock_u3 = mock.create_autospec(u3.U3)
    self.labjack.u3 = self.mock_u3

  def testReadValues(self):
    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def _binaryToCalibratedAnalogVoltage(result, isLowVoltage, channelNumber):
      if channelNumber in self.labjack.HIGH_VOLTAGE_CHANNELS:
        self.assertFalse(isLowVoltage)
      else:
        self.assertTrue(isLowVoltage)
      mapping = {32816: 1.5,
                 35696: 2.7,
                 32827: 3.9,
                 39968: 1.4}
      return mapping[result]
    # pylint: enable=invalid-name
    # pylint: enable=unused-argument
    self.mock_u3.getTemperature.return_value = 298.73988991230726
    self.mock_u3.getFeedback.side_effect = [[32816], [35696], [32827], [39968]]
    self.mock_u3.binaryToCalibratedAnalogVoltage.side_effect = (
        _binaryToCalibratedAnalogVoltage)
    self.labjack.ReadValues()
    point = gps_pb2.Point().FromString(self.point_queue.get())
    self.assertEqual(78.061801842153101916, point.labjack_temp_f)
    self.assertEqual(1.5, point.fuel_level_voltage)
    self.assertEqual(2.7, point.water_temp_voltage)
    self.assertEqual(3.9, point.oil_pressure_voltage)
    self.assertEqual(14.0, point.battery_voltage)


if __name__ == '__main__':
  absltest.main()
