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
import datetime
import multiprocessing
import time
import unittest

import mock
from absl import flags
from absl.testing import absltest

from exit_speed import common_lib
from exit_speed import data_logger
from exit_speed import exit_speed_pb2
from exit_speed import sensor
from exit_speed import tracks

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
    point = exit_speed_pb2.Gps()
    point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    queue = multiprocessing.Queue()
    session = common_lib.Session(
      time=point.time.ToDatetime(),
      track=tracks.portland_internal_raceways.PortlandInternationalRaceway,
      car='RC Car',
      live_data=False)
    sensor_instance = SensorTest(
       point.time.ToDatetime(), {}, queue, start_process=False)
    expected = '/tmp/RC Car/Portland International Raceway/2020-05-23T17:47:44.100000/SensorTest'
    self.assertEqual(expected, sensor.GetLogFilePrefix(
       session, sensor_instance, point))

  def testLogMessage(self):
    point = exit_speed_pb2.Gps()
    point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    queue = multiprocessing.Queue()
    session = common_lib.Session(
      time=point.time.ToDatetime(),
      track=tracks.portland_internal_raceways.PortlandInternationalRaceway,
      car='RC Car',
      live_data=False)
    sensor_instance = SensorTest(
        session, {}, queue, start_process=False)
    sensor_instance.LogMessage(point)
    reader = data_logger.Logger(sensor_instance.data_logger.file_prefix)
    for proto in reader.ReadProtos():
      self.assertEqual(point, read_point)


if __name__ == '__main__':
  absltest.main()
