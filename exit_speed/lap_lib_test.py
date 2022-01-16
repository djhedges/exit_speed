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
"""Unitests for lab_lib.py"""
import unittest

import mock
from absl.testing import absltest

from exit_speed import common_lib
from exit_speed import gps_pb2
from exit_speed import lap_lib



class TestLapLib(unittest.TestCase):
  """Lap time unittests."""

  def testGetPriorUniquePoint(self):
    point_c = gps_pb2.Point()
    point_c.time.FromMilliseconds(10)
    lap = gps_pb2.Lap()
    point = lap.points.add()
    point.time.FromMilliseconds(9)
    point = lap.points.add()
    point.time.FromMilliseconds(9)
    point = lap.points.add()
    point.time.FromMilliseconds(8)
    returned = lap_lib.GetPriorUniquePoint(lap, point_c)
    self.assertEqual(8, returned.time.ToMilliseconds())

  def testSolvePointBAngle(self):
    point_b = gps_pb2.Point()
    point_b.start_finish_distance = 8
    point_c = gps_pb2.Point()
    point_c.start_finish_distance = 6
    with mock.patch.object(common_lib, 'PointDelta') as mock_delta:
      mock_delta.return_value = 7
      self.assertEqual(46.56746344221023,
                       lap_lib.SolvePointBAngle(point_b, point_c))

  def testCalcAcceleration(self):
    point_b = gps_pb2.Point()
    point_b.speed = 70
    point_b.time.FromMilliseconds(1)
    point_c = gps_pb2.Point()
    point_c.speed = 72
    point_c.time.FromMilliseconds(2)
    self.assertEqual(1999.9999999999998,
                     lap_lib.CalcAcceleration(point_b, point_c))

  def testPerpendicularDistanceToFinish(self):
    point_b_angle = 60
    point_b = gps_pb2.Point()
    point_b.start_finish_distance = 1000
    self.assertEqual(500.0000000000001,
                     lap_lib.PerpendicularDistanceToFinish(point_b_angle,
                                                           point_b))

  def testSolveTimeToCrossFinish(self):
    point_b = gps_pb2.Point()
    point_b.speed = 70
    acceleration = 2
    perp_dist_b = 1
    self.assertEqual(0.014282800023195819,
                     lap_lib.SolveTimeToCrossFinish(point_b,
                                                    perp_dist_b,
                                                    acceleration))

  def testGetTimeDelta(self):
    point_b = gps_pb2.Point()
    point_b.time.FromMilliseconds(1)
    point_c = gps_pb2.Point()
    point_c.time.FromMilliseconds(2)
    self.assertEqual(1 * 1e6, lap_lib.GetTimeDelta(point_b, point_c))

  def testCalcTimeAfterFinish(self):
    start_finish = gps_pb2.Point()
    start_finish.lat = 45.595015
    start_finish.lon = -122.694526
    lap = gps_pb2.Lap()
    point_b = lap.points.add()
    point_c = lap.points.add()
    point_b.time.FromMilliseconds(1)
    point_c.time.FromMilliseconds(2)
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    point_b.start_finish_distance = common_lib.PointDelta(start_finish, point_b)
    point_c.start_finish_distance = common_lib.PointDelta(start_finish, point_c)
    point_b.speed = 70
    point_c.speed = 70.2
    self.assertEqual(1000000.0548742702, lap_lib.CalcTimeAfterFinish(lap))

  def testCalcLastLapDuration(self):
    start_finish = gps_pb2.Point()
    start_finish.lat = 45.595015
    start_finish.lon = -122.694526
    session = gps_pb2.Session()
    lap = session.laps.add()
    point_y = lap.points.add()
    point_z = lap.points.add()
    point_y.time.FromMilliseconds(1)
    point_z.time.FromMilliseconds(2)
    point_y.lat = 45.594988
    point_y.lon = -122.694587
    point_z.lat = 45.595000
    point_z.lon = -122.694638
    point_y.start_finish_distance = common_lib.PointDelta(start_finish, point_y)
    point_z.start_finish_distance = common_lib.PointDelta(start_finish, point_z)
    point_y.speed = 70
    point_z.speed = 70.2
    self.assertEqual(1.0 * 1e6, lap_lib.CalcLastLapDuration(session))

    lap = session.laps.add()
    point_a = point_z
    lap.points.append(point_a)
    point_b = lap.points.add()
    point_c = lap.points.add()
    point_b.time.FromMilliseconds(3)
    point_c.time.FromMilliseconds(4)
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    point_b.start_finish_distance = common_lib.PointDelta(start_finish, point_b)
    point_c.start_finish_distance = common_lib.PointDelta(start_finish, point_c)
    point_b.speed = 70
    point_c.speed = 70.2
    self.assertEqual(2000000, lap_lib.CalcLastLapDuration(session))

if __name__ == '__main__':
  absltest.main()
