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
from absl.testing import absltest
import config_lib
import labjack
import mock
import u3


class TestLabjack(unittest.TestCase):
  """Unitests for Labjack."""

  def setUp(self):
    super().setUp()
    config = config_lib.LoadConfig('testdata/test_labjack_config.yaml')
    self.labjack = labjack.Labjack(config, start_process=False)
    self.mock_u3 = mock.create_autospec(u3.U3)
    self.labjack.u3 = self.mock_u3

  def testBuildCommands(self):
    expected_cmds = [u3.AIN(0), u3.AIN(1), u3.AIN(2)]
    commands, command_proto_field = self.labjack.BuildCommands()
    for command in commands:
      index = commands.index(command)
      self.assertEqual(command.positiveChannel,
                       expected_cmds[index].positiveChannel)
    expected_mapping = {0: 'fuel_level_voltage',
                        1: 'water_temp_voltage',
                        2: 'oil_pressure_voltage'}
    for command in command_proto_field:
      self.assertEqual(expected_mapping[command.positiveChannel],
                       command_proto_field[command])

  def testBuildValues(self):
    expected = {'fuel_level_voltage': None,
                'water_temp_voltage': None,
                'oil_pressure_voltage': None}
    self.assertEqual(expected.keys(), self.labjack.BuildValues().keys())

  def testReadValues(self):
    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
    def _binaryToCalibratedAnalogVoltage(result, isLowVoltage, channelNumber):
      self.assertFalse(isLowVoltage)
      mapping = {32816: 1.5,
                 35696: 2.7,
                 32827: 3.9}
      return mapping[result]
    # pylint: enable=invalid-name
    # pylint: enable=unused-argument
    self.mock_u3.getFeedback.return_value = [32816, 35696, 32827]
    self.mock_u3.binaryToCalibratedAnalogVoltage.side_effect = (
        _binaryToCalibratedAnalogVoltage)
    self.labjack.ReadValues()
    self.assertEqual(1.5,
                     self.labjack.voltage_values['fuel_level_voltage'].value)
    self.assertEqual(2.7,
                     self.labjack.voltage_values['water_temp_voltage'].value)
    self.assertEqual(3.9,
                     self.labjack.voltage_values['oil_pressure_voltage'].value)


if __name__ == '__main__':
  absltest.main()
