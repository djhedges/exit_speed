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
"""Common library unittest."""
import unittest

from absl.testing import absltest

from exit_speed import common_lib
from exit_speed import exit_speed_pb2


class TestExitSpeed(unittest.TestCase):
  """Common library unittest."""

  def testPointDelta(self):
    proto_a = exit_speed_pb2.Gps()
    proto_b = exit_speed_pb2.Gps()
    proto_a.lat = 1.1
    proto_b.lat = 2.2
    proto_a.lon = -1.1
    proto_b.lon = -2.2
    self.assertEqual(171979.02735070087,
                     common_lib.PointDelta(proto_a, proto_b))


if __name__ == '__main__':
  absltest.main()
