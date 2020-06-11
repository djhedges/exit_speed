#!/usr/bin/python3

import datetime
import logging
import os
import time
import adafruit_dotstar
import board
import log_files
import gps_pb2
from gps import gps
from gps import WATCH_ENABLE
from gps import WATCH_NEWSTYLE
from gps import EarthDistanceSmall
import numpy as np
from scipy.spatial import cKDTree

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
	       start_speed=4.5,  # 4.5 m/s ~ 10 mph
         start_finish_range=10,  # Meters, ~2x the width of straightaways.
         min_points_per_session=60 * 10,  # 1 min @ gps 10hz
         led_update_interval=1,
	       ):
    """Initializer.

    Args:
      start_speed: Minimum speed before logging starts.
      start_finish_range: Maximum distance a point can be considered when
                          determining if the car crosses the start/finish.
      min_points_per_session:  Used to prevent sessions from prematurely ending.
      led_update_interval:  Controls how often the LEDs can change so as to not
                            enduce epileptic siezures.
    """
    self.dots = adafruit_dotstar.DotStar(board.SCK, board.MOSI, 10,
                                         brightness=0.1)
    self.dots.fill((0, 0, 255))
    self.start_speed = start_speed
    self.start_finish_range = start_finish_range
    self.min_points_per_session = min_points_per_session
    self.led_update_interval = led_update_interval

    self.recording = False

    self.session = None
    self.lap = None
    self.point = None
    self.best_lap = None
    self.tree = None
    self.last_led_update = time.time()

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

  def FindNearestBestLapPoint(self):
    """Returns the nearest point on the best lap to the given point."""
    point = self.GetPoint()
    _, neighbor = self.tree.query([point.lon, point.lat], 1)
    x = self.tree.data[:, 0][neighbor]
    y = self.tree.data[:, 1][neighbor]
    for point_b in self.best_lap.points:
      if point_b.lon == x and point_b.lat == y:
        return point_b

  def LedInterval(self):
    """Returns True if it is safe to update the LEDs based on interval."""
    now = time.time()
    if now - self.last_led_update > self.led_update_interval:
      self.last_led_update = now
      return True
    return False

  def UpdateLeds(self):
    """Update LEDs based on speed difference to the best lap."""
    if self.tree and self.LedInterval():
      point = self.GetPoint()
      best_point = self.FindNearestBestLapPoint()
      if point.speed > best_point.speed:
        led_color = (0, 255, 0)  # Green
      else:
        led_color = (255, 0, 0)  # Red
      speed_delta = abs(point.speed - best_point.speed)
      tenths = speed_delta // 0.1
      if not tenths:
        self.dots.fill((0, 0, 0))
      elif speed_delta < 10 and speed_delta < 1:
        self.dots.fill((0, 0, 0))
        for led_index in range(int(tenths)):
          self.dots[led_index] = led_color
      else:
        self.dots.fill(led_color)

  def ProcessPoint(self):
    """Populates the session with the latest GPS point."""
    point = self.GetPoint()
    session = self.GetSession()
    point.start_finish_distance = PointDelta(point, session.start_finish)
    self.UpdateLeds()

  def SetBestLap(self, lap):
    """Sets best lap and builds a KDTree for finding closest points."""
    if (not self.best_lap or
        lap.duration.ToNanoseconds() < self.best_lap.duration.ToNanoseconds()):
      self.best_lap = lap
      x_y_points = []
      for point in lap.points:
        x_y_points.append([point.lon, point.lat])
      self.tree = cKDTree(np.array(x_y_points))

  def SetLapTime(self):
    """Sets the lap duration based on the first and last point time delta."""
    lap = self.GetLap()
    first_point = lap.points[0]
    last_point = lap.points[-1]
    delta = last_point.time.ToNanoseconds() - first_point.time.ToNanoseconds()
    lap.duration.FromNanoseconds(delta)

    session = self.GetSession()
    self.SetBestLap(lap)

  def CrossStartFinish(self):
    """Checks and handles when the car corsses the start/finish."""
    lap = self.GetLap()
    session = self.GetSession()
    if len(lap.points) > self.min_points_per_session:
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
    self.ProcessPoint()
    lap = self.GetLap()
    lap.points.append(point)
    self.CrossStartFinish()

  def ProcessSession(self):
    """Start/ends the logging of data to log files based on car speed."""
    point = self.GetPoint()
    session = self.GetSession()
    if point.speed > self.start_speed:
      self.ProcessLap()
      if not self.recording:
        self.recording = True
        logging.info('Starting recording')
    if point.speed < self.start_speed and self.recording:
      log_files.SaveSessionToDisk(session)
      self.recording = False
      logging.info('Stopping recording, saving files')

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
                      stream=sys.stdout,
                      level=logging.INFO)
  print(f'Logging to {filename}')
  try:
    while True:
      logging.info('Starting Run')
      es = ExitSpeed()
      es.Run()


  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    logging.info('Done.\nExiting.')
    gpsd.close()
