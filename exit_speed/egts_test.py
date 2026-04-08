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
"""Unitests for egts.py"""
import datetime
import multiprocessing
import unittest
from absl.testing import absltest
from exit_speed import egts
from exit_speed import exit_speed_pb2
from exit_speed import postgres_test_lib


class TestEgts(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Egts unittests."""

  def setUp(self):
    super().setUp()
    self.start_time = datetime.datetime.now()
    self.config = {'car': 'corrado', 'can': {'frequency_hz': 10}}
    self.point_queue = multiprocessing.Queue()
    self.can_data_queue = multiprocessing.Queue()
    self.egts = egts.Egts(self.start_time, self.config,
                         self.point_queue, self.can_data_queue)

  def testParseEgtsFrame(self):
    # 1797 holds EGT 1-4
    # 100 C = 400 raw = 0x0190 -> 212.0 F
    # 101 C = 404 raw = 0x0194 -> 213.8 F
    # 102 C = 408 raw = 0x0198 -> 215.6 F
    # 103 C = 412 raw = 0x019C -> 217.4 F
    data = [0x01, 0x90, 0x01, 0x94, 0x01, 0x98, 0x01, 0x9C]
    self.egts.ParseEgtsFrame(1797, bytes(data))
    self.assertAlmostEqual(212.0, self.egts.egts_proto.egt_1_f)
    self.assertAlmostEqual(213.8, self.egts.egts_proto.egt_2_f)
    self.assertAlmostEqual(215.6, self.egts.egts_proto.egt_3_f)
    self.assertAlmostEqual(217.4, self.egts.egts_proto.egt_4_f)

    # 1798 holds EGT 5-8 (we only use 5-6)
    # 104 C = 416 raw = 0x01A0 -> 219.2 F
    # 105 C = 420 raw = 0x01A4 -> 221.0 F
    data = [0x01, 0xA0, 0x01, 0xA4, 0x00, 0x00, 0x00, 0x00]
    self.egts.ParseEgtsFrame(1798, bytes(data))
    self.assertAlmostEqual(219.2, self.egts.egts_proto.egt_5_f)
    self.assertAlmostEqual(221.0, self.egts.egts_proto.egt_6_f)


if __name__ == '__main__':
  absltest.main()
