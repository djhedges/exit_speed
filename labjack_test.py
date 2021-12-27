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
import unittest

import mock
import u3
from absl.testing import absltest

import config_lib
import labjack


class TestLabjack(unittest.TestCase):
  """Unitests for Labjack."""

  def setUp(self):
    super().setUp()
    config = config_lib.LoadConfig('testdata/test_labjack_config.yaml')
    self.labjack = labjack.Labjack(config, start_process=False)
    self.mock_u3 = mock.create_autospec(u3.U3)
    self.labjack.u3 = self.mock_u3

  def testBuildValues(self):
    expected = {'fuel_level_voltage': None,
                'water_temp_voltage': None,
                'oil_pressure_voltage': None,
                'battery_voltage': None}
    self.assertSequenceEqual(list(expected.keys()),
                             list(self.labjack.BuildValues().keys()))

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
    self.assertEqual(78.061801842153101916, self.labjack.labjack_temp_f.value)
    self.assertEqual(1.5,
                     self.labjack.voltage_values['fuel_level_voltage'].value)
    self.assertEqual(2.7,
                     self.labjack.voltage_values['water_temp_voltage'].value)
    self.assertEqual(3.9,
                     self.labjack.voltage_values['oil_pressure_voltage'].value)
    self.assertEqual(14.0,
                     self.labjack.voltage_values['battery_voltage'].value)


if __name__ == '__main__':
  absltest.main()
