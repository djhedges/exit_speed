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
"""Unitests for gopro.py"""

import mock
import unittest
from absl.testing import absltest
import gopro
import gps_pb2
import pygatt


class TestGopro(unittest.TestCase):
  """GoPro unittests."""

  def setUp(self):
    mock_adapter = mock.create_autospec(pygatt.GATTToolBackend)
    with mock.patch.object(pygatt, 'GATTToolBackend') as mock_backend:
      mock_backend.return_value = mock_adapter
      self.gopro = gopro.GoPro('aa:bb:cc:dd:ee:ff')

  def testProcessPoint(self):
    point = gps_pb2.Point()
    with self.subTest(name='Do not record yet'):
      point.speed = 4.4  # ~10 mph
      point.time.FromJsonString(u'2020-05-23T17:47:44.000Z')
      self.gopro.ProcessPoint(point)
      self.assertFalse(self.gopro.recording)

    with self.subTest(name='Start Recording'):
      with mock.patch.object(self.gopro, 'Start') as mock_start:
        point.speed = 22  # ~50 mph
        point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
        self.gopro.ProcessPoint(point)
        self.assertTrue(self.gopro.recording)
        mock_start.assert_called_once_with()

    with self.subTest(name='Keep Recording'):
      point.speed = 23  # ~51 mph
      point.time.FromJsonString(u'2020-05-23T17:47:44.200Z')
      self.gopro.ProcessPoint(point)
      self.assertTrue(self.gopro.recording)

    with self.subTest(name='Keep Recording Speed below min'):
      point.speed = 4.4  # ~10 mph
      point.time.FromJsonString(u'2020-05-23T17:47:44.300Z')
      self.gopro.ProcessPoint(point)
      self.assertTrue(self.gopro.recording)

    with self.subTest(name='Stop Recording'):
      with mock.patch.object(self.gopro, 'Stop') as mock_stop:
        self.gopro.last_speed_threshold = (
            # 1 Second over the FLAGS.stop_recording_duration_minutes.
            point.time.ToSeconds() - 60 * 5 - 1)
        point.speed = 4.4  # ~10 mph
        point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
        self.gopro.ProcessPoint(point)
        self.assertFalse(self.gopro.recording)
        mock_stop.assert_called_once_with()

    with self.subTest(name='ReStart Recording'):
      with mock.patch.object(self.gopro, 'Start') as mock_start:
        point.speed = 22  # ~50 mph
        point.time.FromJsonString(u'2020-05-24T17:47:44.100Z')
        self.gopro.ProcessPoint(point)
        self.assertTrue(self.gopro.recording)
        mock_start.assert_called_once_with()


if __name__ == '__main__':
  absltest.main()
