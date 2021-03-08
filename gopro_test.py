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
import time
import unittest
from absl.testing import absltest
import gopro
import pygatt


class TestGopro(unittest.TestCase):
  """GoPro unittests."""

  def setUp(self):
    mock_adapter = mock.create_autospec(pygatt.GATTToolBackend)
    with mock.patch.object(pygatt, 'GATTToolBackend') as mock_backend:
      mock_backend.return_value = mock_adapter
      self.gopro = gopro.GoPro('aa:bb:cc:dd:ee:ff', start_process=False)
      self.gopro.last_speed_threshold = time.time()
      self.gopro._ConnectToCamera()

  def testKeepRecordingCheck(self):
    with self.subTest(name='Do not record yet'):
      self.gopro.AppendSpeed(10)
      self.gopro.KeepRecordingCheck()
      self.assertFalse(self.gopro.recording)

    with self.subTest(name='Start Recording'):
      with mock.patch.object(self.gopro, 'Start') as mock_start:
        self.gopro.AppendSpeed(50)
        self.gopro.KeepRecordingCheck()
        self.assertTrue(self.gopro.recording)
        mock_start.assert_called_once_with()

    with self.subTest(name='Keep Recording'):
      self.gopro.AppendSpeed(51)
      self.gopro.KeepRecordingCheck()
      self.assertTrue(self.gopro.recording)

    with self.subTest(name='Keep Recording Speed below min'):
      self.gopro.AppendSpeed(10)
      self.gopro.KeepRecordingCheck()
      self.assertTrue(self.gopro.recording)

    with self.subTest(name='Stop Recording'):
      with mock.patch.object(self.gopro, 'Stop') as mock_stop:
        # 1 Second over the FLAGS.stop_recording_duration_minutes.
        self.gopro.AppendSpeed(10)
        self.gopro.last_speed_threshold = time.time() - 60 * 5 - 1
        self.gopro.KeepRecordingCheck()
        self.assertFalse(self.gopro.recording)
        mock_stop.assert_called_once_with()

    with self.subTest(name='ReStart Recording'):
      with mock.patch.object(self.gopro, 'Start') as mock_start:
        self.gopro.AppendSpeed(50)
        self.gopro.KeepRecordingCheck()
        self.assertTrue(self.gopro.recording)
        mock_start.assert_called_once_with()


if __name__ == '__main__':
  absltest.main()
