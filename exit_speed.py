#!/usr/bin/python

import os
import log_files
import gps_pb2
from gps import gps
from gps import WATCH_ENABLE
from gps import WATCH_NEWSTYLE
from gps import EarthDistanceSmall

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

TRACKS = {(45.695079, -121.525848): 'Test Parking Lot',
          (45.363799, -120.744556): 'Oregon Raceway Park',
          (45.595015, -122.694526): 'Portland International Raceway',
          (47.254702, -123.192676): 'The Ridge Motorsport Park',
          (47.321082, -122.149664): 'Pacific Raceway',
          (47.661806, -117.572297): 'Spokane Raceway'}


def PointDelta(point_a, point_b):
  return EarthDistanceSmall((point_a.lat, point_a.lon),
                            (point_b.lat, point_b.lon))


def FindClosestTrack(point):
  distance_track = []
  for location, track in TRACKS.items():
    lat, lon = location
    track_point = gps_pb2.Point()
    track_point.lat = lat
    track_point.lon = lon
    distance = PointDelta(point, track_point)
    distance_track.append((distance, track, track_point))
  return sorted(distance_track)[0]


class ExitSpeed(object):

  def __init__(self,
	       start_speed=4.5,  # 4.5 ms/ ~ 10 mph
	       ):
    self.start_speed = start_speed

    self.recording = False

    self.session = None
    self.lap = None
    self.point = None

  def GetPoint(self):
    return self.point

  def GetLap(self):
    if not self.lap:
      session = self.GetSession()
      lap = session.laps.add()
      self.lap = lap
    return self.lap

  def GetSession(self):
    if not self.session:
      self.session = gps_pb2.Session()
      _, track, start_finish = FindClosestTrack(self.GetPoint())
      self.session.track = track
      self.session.start_finish.lat = start_finish.lat
      self.session.start_finish.lon = start_finish.lon
    return self.session

  def ProcessPoint(self):
    point = self.GetPoint()
    session = self.GetSession()
    point.start_finish_distance = PointDelta(point, session.start_finish)

  def CrossStartFinish(self):
    lap = self.GetLap()
    session = self.GetSession()
    if len(lap.points) > 2:
      point_a = lap.points[-3]
      point_b = lap.points[-2]
      point_c = lap.points[-1]
      if (point_a.start_finish_distance > point_b.start_finish_distance and
          point_c.start_finish_distance > point_b.start_finish_distance):
        # Add a new lap and set it to self.lap.
        lap = session.laps.add()
        self.lap = lap

  def ProcessLap(self):
    point = self.GetPoint()
    lap = self.GetLap()
    lap.points.append(point)
    self.ProcessPoint()
    self.CrossStartFinish()

  def ProcessSession(self):
    point = self.GetPoint()
    session = self.GetSession()
    if point.speed > self.start_speed:
      self.ProcessLap()
      self.recording = True
    if point.speed < self.start_speed and self.recording:
      log_files.SaveSessionToDisk(session)

  def PopulatePoint(self, report):
    point = gps_pb2.Point()
    point.lat = report.lat
    point.lon = report.lon
    point.alt = report.alt
    point.speed = report.speed
    point.time.FromJsonString(report.time)
    self.point = point

  def ProcessReport(self, report):
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      point = self.PopulatePoint(report)
      self.ProcessSession()

  def Run(self):
    while True:
      report = gpsd.next()
      self.ProcessReport(report)

if __name__ == '__main__':
  try:
    while True:
      es = ExitSpeed()
      es.Run()


  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "Done.\nExiting."
    gpsd.close()
