#!/usr/bin/python

from gps import client
import gps_pb2
import exit_speed
import log_files
import mock
import unittest


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

  def testGetPoint(self):
    point = gps_pb2.Point()
    es = exit_speed.ExitSpeed()
    es.point = point
    self.assertEqual(point, es.GetPoint())

  def testGetLap(self):
    lap = gps_pb2.Lap()
    es = exit_speed.ExitSpeed()
    self.assertTrue(es.GetLap())
    es.lap = lap
    self.assertEqual(lap, es.GetLap())

  def testGetSession(self):
    session = gps_pb2.Session()
    es = exit_speed.ExitSpeed()
    self.assertTrue(es.GetSession())
    es.session = session
    self.assertEqual(session, es.GetSession())

  def testProcessLap(self):
    point = gps_pb2.Point()
    lap = gps_pb2.Lap()
    es = exit_speed.ExitSpeed()
    es.point = point
    es.lap = lap
    es.ProcessLap()
    for lap_point in lap.points:
      self.assertEqual(point, lap_point)

  def testProcessSession(self):
    point = gps_pb2.Point()
    point.speed = 21
    lap = gps_pb2.Lap()
    session = gps_pb2.Session()
    es = exit_speed.ExitSpeed()
    es.point = point
    es.session = session
    es.ProcessSession()
    self.assertTrue(es.recording)

    for session_lap in session.laps:
      for lap_point in lap.points:
        self.assertEqual(point, lap_point)

    point = gps_pb2.Point()
    point.speed = 1
    es.point = point
    with mock.patch.object(log_files, 'SaveSessionToDisk') as mock_save:
      es.ProcessSession()
      mock_save.assert_called_once_with(session)

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
    point = es.GetPoint()
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
    point = es.GetPoint()
    self.assertEqual(point.lat, 14.2)
    self.assertEqual(point.lon, -2.1)
    self.assertEqual(point.alt, 6.9)
    self.assertEqual(point.speed, 0.088)
    self.assertEqual(point.time.seconds, 1576733064)
    self.assertEqual(point.time.nanos, 100000000)

if __name__ == '__main__':
  unittest.main()
