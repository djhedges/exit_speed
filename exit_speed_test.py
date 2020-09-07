#!/usr/bin/python3

import unittest
import exit_speed
from gps import client
import gps_pb2
import mock
import tensorflow as tf


class TestExitSpeed(unittest.TestCase):

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

  def testGetLedColor(self):
    es = exit_speed.ExitSpeed()
    es.speed_deltas.extend([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    self.assertTupleEqual(es.GetLedColor(), (255, 0, 0))
    es.speed_deltas.extend([0, -1, -2, -3, -4, -5, -6, -7, -8, -9])
    self.assertTupleEqual(es.GetLedColor(), (0, 255, 0))
    es.speed_deltas.extend([0, 1, 2, 3, 4, -5, -6, -7, -8, -9])
    self.assertTupleEqual(es.GetLedColor(), (0, 255, 0))

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
    self.assertEqual(14083839.944018112, point.start_finish_distance)

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
    self.assertEqual(es.best_lap, lap)

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
      es = exit_speed.ExitSpeed(min_points_per_session=1)
      es.lap = lap
      es.session = session
      es.CrossStartFinish()
      self.assertEqual(expected_len_of_laps, len(es.session.laps))

  def testProcessLap(self):
    es = exit_speed.ExitSpeed()
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
  unittest.main()
