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
"""Unitests for gps_sensor.py"""
import multiprocessing
import unittest

import gps
import mock
from absl.testing import absltest

from exit_speed import gps_pb2
from exit_speed import gps_sensor


TEST_REPORT_VALUES = {
    u'epx': 7.409,
    u'epy': 8.266,
    u'epv': 20.01,
    u'ept': 0.005,
    u'lon': -2.1,
    u'eps': 165.32,
    u'lat': 14.2,
    u'track': 0.0,
    u'mode': 3,
    u'time': u'2019-12-19T05:24:24.100Z',
    u'device': u'/dev/ttyACM0',
    u'alt': 6.9,
    u'speed': 0.088,
    u'class': u'TPV'}
TEST_REPORT = gps.client.dictwrapper(TEST_REPORT_VALUES)


class TestGPSSensor(unittest.TestCase):
  """GPS Sensor unittests."""

  def testCheckReportFields(self):
    sensor = gps_sensor.GPS()
    with self.subTest(name='Populated Report'):
      self.assertTrue(sensor.CheckReportFields(TEST_REPORT))
    with self.subTest(name='Empty Report'):
      report = gps.client.dictwrapper({})
      self.assertFalse(sensor.CheckReportFields(report))

  def testGetReport(self):
    mock_gpsd = mock.create_autospec(gps.gps)
    sensor = gps_sensor.GPS(mock_gpsd)
    with self.subTest(name='Populated Report'):
      mock_gpsd.next.return_value = TEST_REPORT
      self.assertEqual(TEST_REPORT, sensor.GetReport())
      with self.subTest(name='Duplicate GPS report'):
        self.assertFalse(sensor.GetReport())
    with self.subTest(name='Empty Report'):
      report = gps.client.dictwrapper({})
      mock_gpsd.next.return_value = report
      self.assertFalse(sensor.GetReport())
    with self.subTest(name='Missing Req Field'):
      values = TEST_REPORT_VALUES.copy()
      del values['lat']
      report = gps.client.dictwrapper(values)
      mock_gpsd.next.return_value = report
      self.assertFalse(sensor.GetReport())

  def testGPSProcessLoop(self):
    point_queue = multiprocessing.Queue()
    with mock.patch.object(gps.gps, 'next') as mock_get:
      mock_get.return_value = TEST_REPORT
      proc = gps_sensor.GPSProcess({}, point_queue)
      while point_queue.empty():
        pass
      proc.Join()
      self.assertEqual(point_queue.qsize(), 1)
      point = gps_pb2.Point().FromString(point_queue.get())
      self.assertEqual(point.lat, TEST_REPORT_VALUES['lat'])
      self.assertEqual(point.lon, TEST_REPORT_VALUES['lon'])
      self.assertEqual(point.alt, TEST_REPORT_VALUES['alt'])
      self.assertEqual(point.speed, TEST_REPORT_VALUES['speed'])

if __name__ == '__main__':
  absltest.main()
