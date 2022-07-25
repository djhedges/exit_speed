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
"""Common libaries."""
import datetime
from typing import NamedTuple
from typing import Text

import gps

from exit_speed import exit_speed_pb2
from exit_speed.tracks import base


class Session(NamedTuple):
  track: base.Track
  time: datetime.datetime
  car: Text
  live_data: bool


def PointDelta(point_a: exit_speed_pb2.Gps,
               point_b: exit_speed_pb2.Gps) -> float:
  """Returns the distance in meters between two points."""
  return gps.EarthDistanceSmall((point_a.lat, point_a.lon),
                                (point_b.lat, point_b.lon))

def PointDeltaFromTrack(track: base.Track, point: exit_speed_pb2.Gps) -> float:
  """Returns the distance in meters between two points."""
  return gps.EarthDistanceSmall((track.start_finish[0],
                                 track.start_finish[1]),
                                (point.lat, point.lon))
