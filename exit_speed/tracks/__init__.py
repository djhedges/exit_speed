#!/usr/bin/python3
# Copyright 2021 Google LLC
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
"""Track list and helper functions."""
from typing import Tuple

import gps

from exit_speed import common_lib
from exit_speed import exit_speed_pb2
from exit_speed.tracks import area27
from exit_speed.tracks import base
from exit_speed.tracks import oregon_raceway_park
from exit_speed.tracks import pacific_raceways
from exit_speed.tracks import portland_internal_raceways
from exit_speed.tracks import spokane_raceway
from exit_speed.tracks import test_track
from exit_speed.tracks import the_ridge

TRACK_LIST = (
    area27.Area27,
    oregon_raceway_park.OregonRacewayPark,
    pacific_raceways.PacificRaceways,
    portland_internal_raceways.PortlandInternationalRaceway,
    spokane_raceway.SpokaneRaceway,
    test_track.TestTrack,
    the_ridge.TheRidge,
    )


def FindClosestTrack(report: gps.client.dictwrapper) -> base.Track:
  """Returns the distance, track and start/finish of the closest track."""
  distance_track = []
  for track in TRACK_LIST:
    lat, lon = track.start_finish
    track_point = exit_speed_pb2.Gps(lat=lat, lon=lon)
    report_point = exit_speed_pb2.Gps(lat=report['lat'],
																			lon=report['lon'])
    distance = common_lib.PointDelta(report_point, track_point)
    distance_track.append((distance, track))
  return sorted(distance_track)[0][1]
