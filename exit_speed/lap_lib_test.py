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
from exit_speed import exit_speed_pb2
from exit_speed import lap_lib
from exit_speed import tracks



class TestLapLib(unittest.TestCase):
  """Lap time unittests."""

  def testGetPriorUniquePoint(self):
    point_c = exit_speed_pb2.Gps()
    point_c.time.FromMilliseconds(10)
    lap = []
    point = exit_speed_pb2.Gps()
    lap.append(point)
    point.time.FromMilliseconds(9)
    point = exit_speed_pb2.Gps()
    lap.append(point)
    point.time.FromMilliseconds(9)
    point = exit_speed_pb2.Gps()
    lap.append(point)
    point.time.FromMilliseconds(8)
    returned = lap_lib.GetPriorUniquePoint(lap, point_c)
    self.assertEqual(8, returned.time.ToMilliseconds())

  def testSolvePointBAngle(self):
    track = tracks.portland_internal_raceways.PortlandInternationalRaceway
    point_b = exit_speed_pb2.Gps(
      lat=45.594980,
      lon=-122.694389)
    point_c = exit_speed_pb2.Gps(
      lat=45.595064,
      lon=-122.694638)
    self.assertEqual(5.682068147351827,
                     lap_lib.SolvePointBAngle(track, point_b, point_c))

  def testCalcAcceleration(self):
    point_b = exit_speed_pb2.Gps()
    point_b.speed_ms = 70
    point_b.time.FromMilliseconds(1)
    point_c = exit_speed_pb2.Gps()
    point_c.speed_ms = 72
    point_c.time.FromMilliseconds(2)
    self.assertEqual(1999.9999999999998,
                     lap_lib.CalcAcceleration(point_b, point_c))

  def testPerpendicularDistanceToFinish(self):
    track = tracks.portland_internal_raceways.PortlandInternationalRaceway
    point_b_angle = 60
    point_b = exit_speed_pb2.Gps(
      lat=45.594980,
      lon=-122.694389)
    self.assertEqual(5.6712016865347605,
                     lap_lib.PerpendicularDistanceToFinish(track,
                                                           point_b_angle,
                                                           point_b))

  def testSolveTimeToCrossFinish(self):
    point_b = exit_speed_pb2.Gps()
    point_b.speed_ms = 70
    acceleration = 2
    perp_dist_b = 1
    self.assertEqual(0.014282800023195819,
                     lap_lib.SolveTimeToCrossFinish(point_b,
                                                    perp_dist_b,
                                                    acceleration))

  def testGetTimeDelta(self):
    point_b = exit_speed_pb2.Gps()
    point_b.time.FromMilliseconds(1)
    point_c = exit_speed_pb2.Gps()
    point_c.time.FromMilliseconds(2)
    self.assertEqual(1 * 1e6, lap_lib.GetTimeDelta(point_b, point_c))

  def testCalcTimeAfterFinish(self):
    track = tracks.portland_internal_raceways.PortlandInternationalRaceway
    start_finish = exit_speed_pb2.Gps()
    start_finish.lat = 45.595015
    start_finish.lon = -122.694526
    lap = []
    point_b = exit_speed_pb2.Gps()
    point_c = exit_speed_pb2.Gps()
    lap.append(point_b)
    lap.append(point_c)
    point_b.time.FromMilliseconds(1)
    point_c.time.FromMilliseconds(2)
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    point_b.speed_ms = 70
    point_c.speed_ms = 70.2
    self.assertEqual(1000000.0548742702,
										 lap_lib.CalcTimeAfterFinish(track, lap))

  def testCalcLastLapDuration(self):
    track = tracks.portland_internal_raceways.PortlandInternationalRaceway
    lap = []
    laps = {1: lap}
    start_finish = exit_speed_pb2.Gps()
    start_finish.lat = 45.595015
    start_finish.lon = -122.694526
    point_y = exit_speed_pb2.Gps()
    point_z = exit_speed_pb2.Gps()
    lap.append(point_y)
    lap.append(point_z)
    point_y.time.FromMilliseconds(1)
    point_z.time.FromMilliseconds(2)
    point_y.lat = 45.594988
    point_y.lon = -122.694587
    point_z.lat = 45.595000
    point_z.lon = -122.694638
    point_y.speed_ms = 70
    point_z.speed_ms = 70.2
    self.assertEqual(1.0 * 1e6, lap_lib.CalcLastLapDuration(track, laps))

    lap = []
    laps[2] = lap
    point_a = point_z
    lap.append(point_a)
    point_b = exit_speed_pb2.Gps()
    point_c = exit_speed_pb2.Gps()
    lap.append(point_b)
    lap.append(point_c)
    point_b.time.FromMilliseconds(3)
    point_c.time.FromMilliseconds(4)
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    point_b.speed_ms = 70
    point_c.speed_ms = 70.2
    self.assertEqual(2000000, lap_lib.CalcLastLapDuration(track, laps))

if __name__ == '__main__':
  absltest.main()
