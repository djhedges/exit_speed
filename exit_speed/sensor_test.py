#!/usr/bin/python3
# Copyright 2022 Google LLC
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
"""Unitests for sensor.py"""
import multiprocessing
import pytz
import time
import unittest

import mock
from absl import flags
from absl.testing import absltest

from exit_speed import data_logger
from exit_speed import gps_pb2
from exit_speed import sensor

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')


class SensorTest(sensor.SensorBase):
    pass


class TestAccelerometer(unittest.TestCase):
  """Accelerometer unittests."""

  def testSleepBasedOnHertz(self):
    now = time.time()
    cycle_time = now - 0.01
    with mock.patch.object(time, 'time') as mock_now:
      mock_now.return_value = now
      self.assertEqual(0.09,
          round(sensor.SleepBasedOnHertz(cycle_time, 10), 2))
      self.assertEqual(0.04,
          round(sensor.SleepBasedOnHertz(cycle_time, 20), 2))
      self.assertEqual(0.99,
          round(sensor.SleepBasedOnHertz(cycle_time, 1), 2))

  def testGetLogFilePrefix(self):
    point = gps_pb2.Point()
    point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    queue = multiprocessing.Queue()
    sensor_instance = SensorTest({}, queue, start_process=False)
    expected = '/tmp/unknown_car/SensorTest/2020-05-23T17:47:44.100000'
    self.assertEqual(expected, sensor.GetLogFilePrefix(sensor_instance, point, tz=pytz.UTC))

  def testLogMessage(self):
    point = gps_pb2.Point()
    point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    queue = multiprocessing.Queue()
    sensor_instance = SensorTest({'car': 'Corrado'}, queue, start_process=False)
    sensor_instance.LogMessage(point)
    reader = data_logger.Logger(sensor_instance.data_logger.file_prefix)
    for proto in reader.ReadProtos():
      self.assertEqual(point, read_point)


if __name__ == '__main__':
  absltest.main()
