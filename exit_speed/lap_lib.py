#!/usr/bin/python3
# Copyright 2020 Douglas Hedges
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
from typing import Dict
from typing import List
from typing import NewType

from exit_speed import common_lib
from exit_speed import exit_speed_pb2
from exit_speed.tracks import base

Seconds = NewType('Seconds', float)
Nanoseconds = NewType('Nanoseconds', float)


def GetPriorUniquePoint(lap: List[exit_speed_pb2.Gps],
                        point_c: exit_speed_pb2.Gps) -> exit_speed_pb2.Gps:
  """Avoids a division by zero if the two points have the same values.

  Older logged data had multiple points at the same time.
  """
  index = -1
  point = lap[-1]
  while (point.time.ToNanoseconds() == point_c.time.ToNanoseconds() or
				 (point.lat == point_c.lat and point.lon == point_c.lon)):
    index -= 1
    point = lap[index]
  return point


def SolvePointBAngle(track: base.Track,
										 point_b: exit_speed_pb2.Gps,
										 point_c:exit_speed_pb2.Gps) -> float:
  """Returns the angle of B."""
  # cos(B) = (c² + a² - b²)/2ca  https://rb.gy/pgi7zm
  a = common_lib.PointDeltaFromTrack(track, point_b)
  b = common_lib.PointDeltaFromTrack(track, point_c)
  c = common_lib.PointDelta(point_b, point_c)
  denominator = 2 * c * a
  if not denominator:
    return 0.0
  cos_b = (c**2 + a**2 - b**2) / denominator
  cos_b = max(-1.0, min(1.0, cos_b))
  return math.degrees(math.acos(cos_b))


def CalcAcceleration(point_b: exit_speed_pb2.Gps,
										 point_c: exit_speed_pb2.Gps) -> float:
  """a = Δv/Δt"""
  return (((point_b.speed_ms - point_c.speed_ms) /
           (point_b.time.ToNanoseconds() - point_c.time.ToNanoseconds())) /
           1e-09)  # Nanoseconds > Seconds.


def PerpendicularDistanceToFinish(track: base.Track,
																	point_b_angle: float,
                                  point_b: exit_speed_pb2.Gps) -> float:
  """

  cos(B) = Adjacent / Hypotenuse
  https://www.mathsisfun.com/algebra/trig-finding-side-right-triangle.html
  """
  start_finish_distance = common_lib.PointDeltaFromTrack(track, point_b)
  return math.cos(math.radians(point_b_angle)) * start_finish_distance


def SolveTimeToCrossFinish(point_b: exit_speed_pb2.Gps,
                           perp_dist_b: float,
                           accelration: float) -> Seconds:
  """
  https://physics.stackexchange.com/questions/134771/deriving-time-from-acceleration-displacement-and-initial-velocity
  """
  if accelration == 0:
    # If acceleration is zero, we can just use time = distance / velocity.
    return Seconds(perp_dist_b / point_b.speed_ms)
  sqrt = math.sqrt(point_b.speed_ms ** 2 + 2 * accelration * perp_dist_b)
  return Seconds((point_b.speed_ms * -1 + sqrt) / accelration)


def GetTimeDelta(first_point: exit_speed_pb2.Gps,
                 last_point: exit_speed_pb2.Gps) -> Nanoseconds:
  return Nanoseconds(last_point.time.ToNanoseconds() -
                     first_point.time.ToNanoseconds())


def CalcTimeAfterFinish(track: base.Track,
												lap: List[exit_speed_pb2.Gps]) -> Nanoseconds:
  """Returns how many nanoseconds between crossing start/finish and the last point.

  This assumes the first/last points of a lap are just past start/finish.
  """
  point_c = lap[-1]
  point_b = GetPriorUniquePoint(lap, point_c)
  point_b_angle = SolvePointBAngle(track, point_b, point_c)
  accelration = CalcAcceleration(point_b, point_c)
  perp_dist_b = PerpendicularDistanceToFinish(track, point_b_angle, point_b)
  time_to_fin = SolveTimeToCrossFinish(point_b, perp_dist_b, accelration)
  delta = GetTimeDelta(point_b, point_c)
  return Nanoseconds(delta - time_to_fin * 1e9)


def CalcLastLapDuration(track: base.Track,
												laps: Dict[int, List[exit_speed_pb2.Gps]]) -> Nanoseconds:
  """Calculates the last lap duration (nanoseconds) for the given session."""
  if len(laps) == 1:
    first_point = laps[1][0]
    last_point = laps[1][-1]
    return GetTimeDelta(first_point, last_point)
  prior_lap = laps[len(laps) - 1]
  current_lap = laps[len(laps)]
  first_point = current_lap[0]
  last_point = current_lap[-1]
  delta = GetTimeDelta(first_point, last_point)
  prior_after = CalcTimeAfterFinish(track, prior_lap)
  current_after = CalcTimeAfterFinish(track, current_lap)
  return Nanoseconds(delta - current_after + prior_after)
