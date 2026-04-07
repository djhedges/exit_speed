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
"""Unitests for ecu.py"""
import datetime
import multiprocessing
import unittest
from unittest import mock
from absl.testing import absltest
from exit_speed import ecu
from exit_speed import exit_speed_pb2
from exit_speed import postgres
from exit_speed import postgres_test_lib


class TestEcu(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Ecu unittests."""

  def setUp(self):
    super().setUp()
    self.start_time = datetime.datetime.now()
    self.config = {'car': 'corrado', 'can': {'frequency_hz': 10}}
    self.point_queue = multiprocessing.Queue()
    self.can_data_queue = multiprocessing.Queue()
    self.ecu = ecu.Ecu(self.start_time, self.config,
                       self.point_queue, self.can_data_queue)

  def testParseLinkDashFrame(self):
    frames = [
      [0, 0, 0, 0, 0, 0, 0, 0],
      [1, 0, 233, 3, 0, 0, 0, 0],
      [2, 0, 0, 0, 0, 0, 91, 0],
      [3, 0, 50, 0, 20, 5, 0, 0],
      [4, 0, 0, 0, 0, 0, 232, 3],
      [5, 0, 0, 0, 0, 0, 0, 0],
      [6, 0, 0, 0, 0, 0, 0, 0],
      [8, 0, 69, 0, 1, 0, 0, 0],
      [9, 0, 0, 0, 0, 0, 0, 0],
      [10, 0, 0, 0, 0, 0, 0, 0],
      [11, 0, 0, 0, 0, 0, 0, 0],
      [12, 0, 0, 0, 0, 0, 0, 0],
      [13, 0, 0, 0, 0, 0, 0, 0],
    ]
    for frame in frames:
      self.ecu.ParseLinkDashFrame(bytes(frame))

    self.assertAlmostEqual(100.1, self.ecu.ecu_proto.barometric_pressure)
    self.assertAlmostEqual(105.8, self.ecu.ecu_proto.ect_f)
    self.assertAlmostEqual(32.0, self.ecu.ecu_proto.iat_f)
    self.assertAlmostEqual(13.0, self.ecu.ecu_proto.ecu_volts)
    self.assertAlmostEqual(66.2, self.ecu.ecu_proto.oil_temp_f)
    self.assertEqual(1, self.ecu.ecu_proto.oil_pressure)


if __name__ == '__main__':
  absltest.main()
