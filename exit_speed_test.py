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

import sys
import unittest
import mock
from absl import flags
from absl.testing import absltest
import fake_rpi
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# Fixes dotstar import on Travis.	import fake_rpi
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
import adafruit_dotstar
import exit_speed
import leds
from gps import client
import gps_pb2
import tensorflow as tf

FLAGS = flags.FLAGS
FLAGS.set_default('config_path', 'testdata/test_config.yaml')


class TestExitSpeed(unittest.TestCase):

  def setUp(self):
￼   super(TestExitSpeed, self).setUp()
￼   mock_star = mock.create_autospec(adafruit_dotstar.DotStar)
￼   patch = mock.patch.object(adafruit_dotstar, 'DotStar')
￼   patch.return_value = mock_star
￼   patch.start()

  def testPointDelta(self):
    point_a = gps_pb2.Point()
    point_b = gps_pb2.Point()
    point_a.lat = 1.1
    point_b.lat = 2.2
    point_a.lon = -1.1
    point_b.lon = -2.2
    self.assertEqual(171979.02735070087,
                     exit_speed.PointDelta(point_a, point_b))

  def testFindClosestTrack(self):
    point = gps_pb2.Point()
    point.lat = 45.595412
    point.lon = -122.693901
    distance, track, _ = exit_speed.FindClosestTrack(point)
    self.assertEqual(65.64651548636733, distance)
    self.assertEqual(track, 'Portland International Raceway')
    self.assertEqual(point.lat, 45.595412)
    self.assertEqual(point.lon, -122.693901)

  def testProcessPoint(self):
    prior_point = gps_pb2.Point()
    prior_point.lat = 12.000000
    prior_point.lon = 23.000000
    point = gps_pb2.Point()
    point.lat = 12.000001
    point.lon = 23.000002
    es = exit_speed.ExitSpeed()
    es.lap = gps_pb2.Lap()
    es.lap.points.extend([prior_point, point])
    es.point = point
    mock_writer = mock.create_autospec(tf.io.TFRecordWriter)
    es.writer = mock_writer
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
    params = ((2, 1, 3, 2),  # Start finish cross.
              (102, 101, 103, 1),  # Too far away.
              )
    for a_distance, b_distance, c_distance, expected_len_of_laps in params:
      point_a = gps_pb2.Point()
      point_b = gps_pb2.Point()
      point_c = gps_pb2.Point()
      point_a.start_finish_distance = a_distance
      point_b.start_finish_distance = b_distance
      point_c.start_finish_distance = c_distance
      session = gps_pb2.Session()
      session.track = 'Portland International Raceway'
      session.start_finish.lat = 45.595015
      session.start_finish.lon = -122.694526
      lap = session.laps.add()
      lap.points.extend([point_a, point_b, point_c])
      es = exit_speed.ExitSpeed()
      es.lap = lap
      es.session = session
      es.CrossStartFinish()
      self.assertEqual(expected_len_of_laps, len(es.session.laps))

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
    mock_writer = mock.create_autospec(tf.io.TFRecordWriter)
    es.writer = mock_writer
    es.ProcessSession()

  def testPopulatePoint(self):
    report = client.dictwrapper({
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

  def testProcessReport(self):
    report = client.dictwrapper({
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


if __name__ == '__main__':
  absltest.main()
