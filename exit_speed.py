#!/usr/bin/python

import datetime
import logging
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
  """Returns the distance between two points."""
  return EarthDistanceSmall((point_a.lat, point_a.lon),
                            (point_b.lat, point_b.lon))


def FindClosestTrack(point):
  """Returns the distance, track and start/finish of the closest track."""
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
  """Main object which loops and logs data."""

  def __init__(self,
	       start_speed=4.5,  # 4.5 ms/ ~ 10 mph
         start_finish_range=10,  # Meters, ~2x the width of straightaways.
	       ):
    """Initializer.

    Args:
      start_speed: Minimum speed before logging starts.
      start_finish_range: Maximum distance a point can be considered when
                          determining if the car crosses the start/finish.
    """
    self.start_speed = start_speed
    self.start_finish_range = start_finish_range

    self.recording = False

    self.session = None
    self.lap = None
    self.point = None

  def GetPoint(self):
    """Returns the latest GPS point."""
    return self.point

  def GetLap(self):
    """Returns the current lap."""
    if not self.lap:
      session = self.GetSession()
      lap = session.laps.add()
      self.lap = lap
    return self.lap

  def GetSession(self):
    """Returns the current session."""
    if not self.session:
      self.session = gps_pb2.Session()
      _, track, start_finish = FindClosestTrack(self.GetPoint())
      logging.info('Closest track: %s' % track)
      self.session.track = track
      self.session.start_finish.lat = start_finish.lat
      self.session.start_finish.lon = start_finish.lon
    return self.session

  def ProcessPoint(self):
    """Populates the session with the latest GPS point."""
    point = self.GetPoint()
    session = self.GetSession()
    point.start_finish_distance = PointDelta(point, session.start_finish)

  def SetLapTime(self):
    """Sets the lap duration based on the first and last point time delta."""
    lap = self.GetLap()
    first_point = lap.points[0]
    last_point = lap.points[-1]
    delta = last_point.time.ToNanoseconds() - first_point.time.ToNanoseconds()
    lap.duration.FromNanoseconds(delta)

  def CrossStartFinish(self):
    """Checks and handles when the car corsses the start/finish."""
    lap = self.GetLap()
    session = self.GetSession()
    if len(lap.points) > 2:
      point_a = lap.points[-3]
      point_b = lap.points[-2]
      point_c = lap.points[-1]  # Latest point.
      if (point_c.start_finish_distance < self.start_finish_range and
          point_a.start_finish_distance > point_b.start_finish_distance and
          point_c.start_finish_distance > point_b.start_finish_distance):
        logging.info('Start/Finish')
        self.SetLapTime()
        # Add a new lap and set it to self.lap.
        lap = session.laps.add()
        self.lap = lap

  def ProcessLap(self):
    """Adds the point to the lap and checks if we crossed start/finish."""
    point = self.GetPoint()
    lap = self.GetLap()
    lap.points.append(point)
    self.ProcessPoint()
    self.CrossStartFinish()

  def ProcessSession(self):
    """Start/ends the logging of data to log files based on car speed."""
    point = self.GetPoint()
    session = self.GetSession()
    if point.speed > self.start_speed:
      self.ProcessLap()
      self.recording = True
    if point.speed < self.start_speed and self.recording:
      log_files.SaveSessionToDisk(session)
      self.recording = False

  def PopulatePoint(self, report):
    """Populates the point protocol buffer."""
    point = gps_pb2.Point()
    point.lat = report.lat
    point.lon = report.lon
    point.alt = report.alt
    point.speed = report.speed
    point.time.FromJsonString(report.time)
    self.point = point

  def ProcessReport(self, report):
    """Processes a GPS report form the sensor.."""
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      self.PopulatePoint(report)
      self.ProcessSession()

  def Run(self):
    """Runs exit speed in a loop."""
    while True:
      report = gpsd.next()
      self.ProcessReport(report)

if __name__ == '__main__':
  today = datetime.datetime.today()
  filename = 'exit_speed-%s' % today.isoformat()
  logging.basicConfig(filename=os.path.join(log_files.LAP_LOGS, filename),
                      level=logging.INFO)
  try:
    while True:
      logging.info('Starting Run')
      es = ExitSpeed()
      es.Run()


  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    logging.info('Done.\nExiting.')
    gpsd.close()
