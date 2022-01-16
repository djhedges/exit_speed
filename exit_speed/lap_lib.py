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
"""Functions related to lap time calculations.

point_c |\
        | \
        |  \
        |   \
        |____\______ start/finish
        |    /
        |   /
        |  /
        |B/
point_b |/
        |
        |
        |
        |
        |
        |
        |
        |
point_a |
"""
# pylint: enable=anomalous-backslash-in-string
import math

from exit_speed import common_lib
from exit_speed import gps_pb2


def GetPriorUniquePoint(lap: gps_pb2.Lap,
                        point_c: gps_pb2.Point) -> gps_pb2.Point:
  """Avoids a division by zero if the two points have the same time.

  Older logged data had multiple points at the same time.
  """
  index = -1
  point = lap.points[-1]
  while point.time.ToNanoseconds() == point_c.time.ToNanoseconds():
    index -= 1
    point = lap.points[index]
  return point


def SolvePointBAngle(point_b, point_c) -> float:
  """Returns the angle of B."""
  dist_b_c = common_lib.PointDelta(point_b, point_c)
  # cos(B) = (c² + a² - b²)/2ca  https://rb.gy/pgi7zm
  a = point_b.start_finish_distance
  b = point_c.start_finish_distance
  c = dist_b_c
  return math.degrees(math.acos((c**2 + a**2 - b**2)/(2*c*a)))


def CalcAcceleration(point_b: gps_pb2.Point, point_c: gps_pb2.Point) -> float:
  """a = Δv/Δt"""
  return (((point_b.speed - point_c.speed) /
           (point_b.time.ToNanoseconds() - point_c.time.ToNanoseconds())) /
           1e-09)  # Nanoseconds > Seconds.


def PerpendicularDistanceToFinish(point_b_angle: float,
                                  point_b: gps_pb2.Point) -> float:
  """

  cos(B) = Adjacent / Hypotenuse
  https://www.mathsisfun.com/algebra/trig-finding-side-right-triangle.html
  """
  return math.cos(math.radians(point_b_angle)) * point_b.start_finish_distance


def SolveTimeToCrossFinish(point_b: gps_pb2.Point,
                           perp_dist_b: float,
                           accelration: float):
  """
  https://physics.stackexchange.com/questions/134771/deriving-time-from-acceleration-displacement-and-initial-velocity
  """
  sqrt = math.sqrt(point_b.speed ** 2 + 2 * accelration * perp_dist_b)
  return (point_b.speed * -1 + sqrt) / accelration


def GetTimeDelta(first_point, last_point) -> float:
  return last_point.time.ToNanoseconds() - first_point.time.ToNanoseconds()


def CalcTimeAfterFinish(lap: gps_pb2.Point) -> float:
  """Returns how many seconds between crossing start/finish and the last point.

  This assumes the first/last points of a lap are just past start/finish.
  """
  point_c = lap.points[-1]
  point_b = GetPriorUniquePoint(lap, point_c)
  point_b_angle = SolvePointBAngle(point_b, point_c)
  accelration = CalcAcceleration(point_b, point_c)
  perp_dist_b = PerpendicularDistanceToFinish(point_b_angle, point_b)
  time_to_fin = SolveTimeToCrossFinish(point_b, perp_dist_b, accelration)
  delta = GetTimeDelta(point_b, point_c)
  return delta - time_to_fin


def CalcLastLapDuration(session: gps_pb2.Session) -> float:
  """Calculates the last lap duration for the given session."""
  if len(session.laps) == 1:
    first_point = session.laps[0].points[0]
    last_point = session.laps[0].points[-1]
    return GetTimeDelta(first_point, last_point)
  prior_lap = session.laps[-2]
  current_lap = session.laps[-1]
  first_point = current_lap.points[0]
  last_point = current_lap.points[-1]
  delta = GetTimeDelta(first_point, last_point)
  prior_after = CalcTimeAfterFinish(prior_lap)
  current_after = CalcTimeAfterFinish(current_lap)
  return int(delta - current_after * 1e9 + prior_after * 1e9)
