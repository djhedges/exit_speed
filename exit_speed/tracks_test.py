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
"""Unitests for tracks."""
import unittest

from absl.testing import absltest

from exit_speed import gps_pb2
from exit_speed import tracks

class TestTracks(unittest.TestCase):
  """Gyroscope unittests."""

  def testFindClosestTrack(self):
    point = gps_pb2.Point()
    point.lat = 45.595412
    point.lon = -122.693901
    distance, track, _ = tracks.FindClosestTrack(point)
    self.assertEqual(65.64651548636733, distance)
    self.assertEqual(track.name, 'Portland International Raceway')
    self.assertEqual(point.lat, 45.595412)
    self.assertEqual(point.lon, -122.693901)


if __name__ == '__main__':
  absltest.main()
