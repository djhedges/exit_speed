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
# pylint: disable=anomalous-backslash-in-string
"""An attempt to improve the accuracy of when start/finish is crossed.

Dusting off old math and physics cobwebs.  This does assume the car was going
straight when crossing start/finish.


point_a |\
        |A\
        |  \
        |   \
        |____\______ start/finish
        |    /
        |   /
        |  /
        |B/
point_b |/
"""
# pylint: enable=anomalous-backslash-in-string

import math
import common_lib
import gps_pb2


def SolveOuterAngles(dist_a_b: float,
                     dist_a_finish: float,
                     dist_b_finish: float):
  """Solve the outer triangle angles.

  cos(A) = (b² + c² - a²)/2bc  https://rb.gy/pgi7zm
  """
  b, c, a = dist_a_b, dist_a_finish, dist_b_finish
  return math.degrees(math.acos((b**2 + c**2 - a**2)/(2*b*c)))


def ImproveDistanceToFinish(point_b_angle: float, dist_b_finish: float):
  """

  cos(B) = Adjacent / Hypotenuse
  https://www.mathsisfun.com/algebra/trig-finding-side-right-triangle.html
  """
  return math.cos(math.radians(point_b_angle)) * dist_b_finish


def CalcAcceleration(point_a: gps_pb2.Point, point_b: gps_pb2.Point):
  """a = Δv/Δt"""
  return (((point_a.speed - point_b.speed) /
           (point_a.time.ToNanoseconds() - point_b.time.ToNanoseconds())) /
           1e-09)  # Nanoseconds > Seconds.



def SolveTimeToCrossFinish(point_b: gps_pb2.Point,
                           improved_b_to_finish: float,
                           accelration: float):
  """
  https://physics.stackexchange.com/questions/134771/deriving-time-from-acceleration-displacement-and-initial-velocity
  """
  sqrt = math.sqrt(point_b.speed ** 2 + 2 * accelration * improved_b_to_finish)
  return (point_b.speed * -1 + sqrt) / accelration

def _GetFirstPoints(lap: gps_pb2.Lap):
  """Avoids a divsion by zero if the two points have the same time.

  Older logged data had multiple points at the same time.
  """
  a_index = 1
  point_b = lap.points[0]
  point_a = lap.points[1]
  while point_b.time.ToNanoseconds() == point_a.time.ToNanoseconds():
    a_index += 1
    point_a = lap.points[a_index]
  return point_a, point_b


def _GetLastPoints(lap: gps_pb2.Lap):
  """Avoids a divsion by zero if the two points have the same time.

  Older logged data had multiple points at the same time.
  """
  b_index = -1
  point_a = lap.points[-1]
  point_b = lap.points[-2]
  while point_b.time.ToNanoseconds() == point_a.time.ToNanoseconds():
    b_index -= 1
    point_b = lap.points[b_index]
  return point_a, point_b


def GetImprovedTimeToFinish(point_a, point_b):
  dist_a_b = common_lib.PointDelta(point_a, point_b)
  point_b_angle = SolveOuterAngles(dist_a_b,
                                   point_a.start_finish_distance,
                                   point_b.start_finish_distance)
  improved_b_to_finish = ImproveDistanceToFinish(point_b_angle,
                                                 point_b.start_finish_distance)
  accelration = CalcAcceleration(point_a, point_b)
  return SolveTimeToCrossFinish(point_b,
                                improved_b_to_finish,
                                accelration)


def ImprovedStartFinishCrossing(lap: gps_pb2.Lap):
  first_point_to_finish = GetImprovedTimeToFinish(*_GetFirstPoints(lap))
  last_point_to_finish = GetImprovedTimeToFinish(*_GetLastPoints(lap))
  first_point = lap.points[0]
  last_point = lap.points[-1]
  duration = (last_point.time.ToNanoseconds() -
              first_point.time.ToNanoseconds() -
              first_point_to_finish * 1e09 +  # Seconds > Nanoseconds.
              last_point_to_finish * 1e09)  # Seconds > Nanoseconds.
  return int(duration)
