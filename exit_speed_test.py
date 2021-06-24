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
"""ExitSpeed unittest."""

import mock
import pytz
import sys
import unittest
from absl import flags
from absl.testing import absltest
import labjack
import gps
import gps_pb2
import psycopg2
import timescale
# pylint: disable=wrong-import-position
import fake_rpi
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# Fixes adafruit_adxl34x import on Travis.
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_dotstar
  import exit_speed
# pylint: enable=wrong-import-position

FLAGS = flags.FLAGS
FLAGS.set_default('config_path', 'testdata/test_config.yaml')
FLAGS.set_default('data_log_path', '/tmp')


class TestExitSpeed(unittest.TestCase):
  """ExitSpeed unittest."""

  def setUp(self):
    super().setUp()
    self._AddMock(adafruit_dotstar, 'DotStar')
    self._AddMock(gps, 'gps')
    mock_conn = mock.create_autospec(psycopg2.extensions.connection)
    mock_connect = self._AddMock(timescale, 'ConnectToDB')
    mock_connect.return_value = mock_conn

  def _AddMock(self, module, name):
    patch = mock.patch.object(module, name)
    self.addCleanup(patch.stop)
    return patch.start()

  def testGetLogFilePrefix(self):
    point = gps_pb2.Point()
    point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    es = exit_speed.ExitSpeed()
    expected = '/tmp/Corrado/2020-05-23T17:47:44.100000'
    self.assertEqual(expected, es.GetLogFilePrefix(point, tz=pytz.UTC))

  def testCalculateElapsedValues(self):
    prior_point = gps_pb2.Point()
    prior_point.lat = 12.000000
    prior_point.lon = 23.000000
    prior_point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    point = gps_pb2.Point()
    point.lat = 12.000001
    point.lon = 23.000002
    point.time.FromJsonString(u'2020-05-23T17:47:44.200Z')
    es = exit_speed.ExitSpeed()
    es.lap = gps_pb2.Lap()
    es.lap.points.extend([prior_point, point])
    es.point = point
    es.ProcessPoint()
    self.assertEqual(prior_point.elapsed_duration_ms, 0)
    self.assertEqual(prior_point.elapsed_distance_m, 0)
    self.assertEqual(point.elapsed_duration_ms, 100)
    self.assertEqual(point.elapsed_distance_m, 0.2430443280901163)

  def testProcessPoint(self):
    prior_point = gps_pb2.Point()
    prior_point.lat = 12.000000
    prior_point.lon = 23.000000
    prior_point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    point = gps_pb2.Point()
    point.lat = 12.000001
    point.lon = 23.000002
    point.time.FromJsonString(u'2020-05-23T17:47:44.200Z')
    es = exit_speed.ExitSpeed()
    es.lap = gps_pb2.Lap()
    es.lap.points.extend([prior_point, point])
    es.point = point
    es.ProcessPoint()
    self.assertEqual(2856514.6203466402, point.start_finish_distance)

  def testSetLapTime(self):
    es = exit_speed.ExitSpeed()
    first_point = gps_pb2.Point()
    first_point.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    last_point = gps_pb2.Point()
    last_point.time.FromJsonString(u'2020-05-23T17:49:00.100Z')
    session = gps_pb2.Session()
    lap = session.laps.add()
    lap.points.append(first_point)
    lap.points.append(last_point)
    es.lap = lap
    es.session = session
    es.SetLapTime()
    self.assertEqual(76, lap.duration.ToSeconds())
    self.assertEqual(es.leds.best_lap, lap)

  def testCrossStartFinish(self):
    point_a = gps_pb2.Point()
    point_b = gps_pb2.Point()
    point_c = gps_pb2.Point()
    point_b.start_finish_distance = 5.613414540798601
    point_c.start_finish_distance = 8.86833983566463
    point_a.time.FromMilliseconds(1000)
    point_b.time.FromMilliseconds(2000)
    point_c.time.FromMilliseconds(3000)
    point_a.lat = 45.594961
    point_a.lon = -122.694508
    point_b.lat = 45.594988
    point_b.lon = -122.694587
    point_c.lat = 45.595000
    point_c.lon = -122.694638
    session = gps_pb2.Session()
    session.track = 'Portland International Raceway'
    session.start_finish.lat = 45.595015
    session.start_finish.lon = -122.694526
    lap = session.laps.add()
    lap.points.extend([point_a, point_b])
    es = exit_speed.ExitSpeed(min_points_per_session=0)
    es.point = point_c
    es.lap = lap
    es.session = session
    es.CrossStartFinish()
    self.assertEqual(2, len(es.session.laps))
    self.assertEqual(2, len(es.session.laps[0].points))
    self.assertEqual(2, len(es.session.laps[1].points))
    self.assertIn(point_a, es.session.laps[0].points)
    self.assertIn(point_b, es.session.laps[0].points)
    self.assertIn(point_b, es.session.laps[1].points)
    self.assertIn(point_c, es.session.laps[1].points)
    self.assertNotIn(point_c, es.session.laps[0].points)

  def testProcessLap(self):
    es = exit_speed.ExitSpeed()
    es.point = es.lap.points.add()
    es.ProcessLap()
    self.assertTrue(es.lap.points)

  def testProcessSession(self):
    point = gps_pb2.Point()
    point.speed = 21
    lap = gps_pb2.Lap()
    session = gps_pb2.Session()
    es = exit_speed.ExitSpeed()
    es.point = point
    es.session = session
    es.ProcessSession()

    for _ in session.laps:
      for lap_point in lap.points:
        self.assertEqual(point, lap_point)

    point = gps_pb2.Point()
    point.speed = 1
    es.point = point
    es.ProcessSession()

  def testReadLabjackValues(self):
    point = gps_pb2.Point()
    es = exit_speed.ExitSpeed()
    es.ReadLabjackValues(point)
    with self.subTest(name='Labjack disabled'):
      self.assertFalse(point.labjack_temp_f)
    with self.subTest(name='Labjack enabled'):
      es.config['labjack'] = {'fio5': 'fuel_level_voltage'}
      es.labjack = labjack.Labjack(es.config)
      es.labjack.labjack_temp_f.value = 78.061801842153101916
      es.labjack.voltage_values['fuel_level_voltage'].value = 1.5
      es.ReadLabjackValues(point)
      self.assertEqual(78.061801842153101916, point.labjack_temp_f)
      self.assertEqual(1.5, point.fuel_level_voltage)

  def testPopulatePoint(self):
    report = gps.client.dictwrapper({
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
        u'class': u'TPV'})
    es = exit_speed.ExitSpeed()
    es.PopulatePoint(report)
    point = es.point
    self.assertEqual(point.lat, 14.2)
    self.assertEqual(point.lon, -2.1)
    self.assertEqual(point.alt, 6.9)
    self.assertEqual(point.speed, 0.088)
    self.assertEqual(point.time.seconds, 1576733064)
    self.assertEqual(point.time.nanos, 100000000)

  def testCheckReportFields(self):
    report = gps.client.dictwrapper({
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
        u'class': u'TPV'})
    es = exit_speed.ExitSpeed()
    with self.subTest(name='Populated Report'):
      self.assertTrue(es.CheckReportFields(report))
    with self.subTest(name='Empty Report'):
      report = gps.client.dictwrapper({})
      self.assertFalse(es.CheckReportFields(report))

  def testProcessReport(self):
    report = gps.client.dictwrapper({
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
        u'class': u'TPV'})
    es = exit_speed.ExitSpeed()
    es.ProcessReport(report)
    point = es.point
    self.assertEqual(point.lat, 14.2)
    self.assertEqual(point.lon, -2.1)
    self.assertEqual(point.alt, 6.9)
    self.assertEqual(point.speed, 0.088)
    self.assertEqual(point.time.seconds, 1576733064)
    self.assertEqual(point.time.nanos, 100000000)
    with self.subTest(name='Empty Report'):
      # Ensure we don't crash if report is missing fields.
      report = gps.client.dictwrapper({})
      es.ProcessReport(report)


if __name__ == '__main__':
  absltest.main()
