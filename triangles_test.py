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
"""Unitests for triangles.py"""

import unittest
from absl.testing import absltest
import gps_pb2
import triangles


class TestTriangles(unittest.TestCase):
  """Triangles unittests."""

  def testSolveOuterAngles(self):
    a = 8
    b = 6
    c = 7
    expected = 57.9100487437197
    self.assertEqual(expected, triangles.SolveOuterAngles(a, b, c))

  def testImproveDistanceToFinish(self):
    self.assertEqual(500, int(triangles.ImproveDistanceToFinish(60, 1000)))

  def testCalcAcceleration(self):
    point_a = gps_pb2.Point()
    point_a.speed = 15
    point_a.time.FromSeconds(5)
    point_b = gps_pb2.Point()
    point_b.speed = 5
    point_b.time.FromSeconds(0)
    self.assertEqual(2, triangles.CalcAcceleration(point_a, point_b))


if __name__ == '__main__':
  absltest.main()
