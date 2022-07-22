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
from absl import flags
from absl.testing import absltest

from exit_speed import config_lib
from exit_speed import exit_speed_pb2
from exit_speed import labjack
from exit_speed import postgres_test_lib

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')


class TestLabjack(postgres_test_lib.PostgresTestBase, unittest.TestCase):
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
    with mock.patch.object(
        self.labjack, 'LogAndExportProto') as mock_log_and_export:
        self.labjack.ReadValues()
    mock_log_and_export.assert_called_once_with(
      exit_speed_pb2.Labjack(
        labjack_temp_f=78.061801842153101916,
        fuel_level_voltage=1.5,
        water_temp_voltage=2.7,
        oil_pressure_voltage=3.9,
        battery_voltage=14.0))


if __name__ == '__main__':
  absltest.main()
