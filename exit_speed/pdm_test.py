#!/usr/bin/python3
# Copyright 2022 Douglas Hedges
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
"""Unitests for pdm.py"""
import datetime
import multiprocessing
import unittest
from absl.testing import absltest
from exit_speed import pdm
from exit_speed import exit_speed_pb2
from exit_speed import postgres_test_lib


class TestPdm(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Pdm unittests."""

  def setUp(self):
    super().setUp()
    self.start_time = datetime.datetime.now()
    self.config = {'car': 'corrado', 'can': {'frequency_hz': 10}}
    self.point_queue = multiprocessing.Queue()
    self.can_data_queue = multiprocessing.Queue()
    self.pdm = pdm.Pdm(self.start_time, self.config,
                       self.point_queue, self.can_data_queue)

  def testParsePdmFrameIO(self):
    # Frame 1: HP Output 1
    # Compound ID 0, Status 1, Freq 100Hz (0x0064), Duty 50.00% (0x1388), Current 10.00A (0x03E8)
    data = [0, 1, 0x00, 0x64, 0x13, 0x88, 0x03, 0xE8]
    self.pdm.ParsePdmFrame(bytes(data))
    self.assertEqual(1, self.pdm.pdm_proto.hp_output_1_status)
    self.assertEqual(100, self.pdm.pdm_proto.hp_output_1_freq)
    self.assertAlmostEqual(50.0, self.pdm.pdm_proto.hp_output_1_duty_cycle)
    self.assertAlmostEqual(10.0, self.pdm.pdm_proto.hp_output_1_current)

    # Frame 5: ADIO 1
    # Compound ID 4, Status 2, Freq 50Hz (0x0032), Duty 25.00% (0x09C4), Voltage 5.00V (0x01F4)
    data = [4, 2, 0x00, 0x32, 0x09, 0xC4, 0x01, 0xF4]
    self.pdm.ParsePdmFrame(bytes(data))
    self.assertEqual(2, self.pdm.pdm_proto.adio_1_status)
    self.assertEqual(50, self.pdm.pdm_proto.adio_1_freq)
    self.assertAlmostEqual(25.0, self.pdm.pdm_proto.adio_1_duty_cycle)
    self.assertAlmostEqual(5.0, self.pdm.pdm_proto.adio_1_voltage)

  def testParsePdmFrameHealth(self):
    # Frame 13: Health (Compound ID 50)
    # Byte 1: Temp 30C (+50 offset = 80), Byte 2: Voltage 13.5V (x10 = 135)
    data = [50, 80, 135, 0, 0, 0, 0, 0]
    self.pdm.ParsePdmFrame(bytes(data))
    # (30 * 9/5) + 32 = 86.0 F
    self.assertAlmostEqual(86.0, self.pdm.pdm_proto.pdm_temp_f)
    self.assertAlmostEqual(13.5, self.pdm.pdm_proto.pdm_voltage)


if __name__ == '__main__':
  absltest.main()
