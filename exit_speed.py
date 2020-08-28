#!/usr/bin/python3

import collections
import datetime
import logging
import os
import statistics
import sys
import time
import adafruit_dotstar
import board
import u3
import gps_pb2
import timescale
from gps import gps
from gps import WATCH_ENABLE
from gps import WATCH_NEWSTYLE
from gps import EarthDistanceSmall
import numpy as np
from sklearn.neighbors import BallTree
import tensorflow as tf

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

TRACKS = {(45.695079, -121.525848): 'Test Parking Lot',
          (45.363799, -120.744556): 'Oregon Raceway Park',
          (45.595015, -122.694526): 'Portland International Raceway',
          (47.254702, -123.192676): 'The Ridge Motorsport Park',
          (47.321082, -122.149664): 'Pacific Raceway',
          (47.661806, -117.572297): 'Spokane Raceway'}

DEFAULT_LOG_PATH = '/home/pi/lap_logs'


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
         data_log_path=DEFAULT_LOG_PATH,
         start_finish_range=10,  # Meters, ~2x the width of straightaways.
         min_points_per_session=60 * 10,  # 1 min @ gps 10hz
         led_update_interval=0.2,
         led_brightness=0.5,
         speed_deltas=50,
         live_data=True,
	       ):
    """Initializer.

    Args:
      start_finish_range: Maximum distance a point can be considered when
                          determining if the car crosses the start/finish.
      min_points_per_session:  Used to prevent sessions from prematurely ending.
      led_update_interval:  Controls how often the LEDs can change so as to not
                            enduce epileptic siezures.
      led_brightness: A percentage of how bright the LEDs should be.
      speed_deltas:  Used to smooth out GPS data.  This controls how many recent
                     speed deltas are stored.  50 at 10hz means a median of the
                     last 5 seconds is used.
    """
    self.data_log_path = data_log_path
    self.start_finish_range = start_finish_range
    self.min_points_per_session = min_points_per_session
    self.led_update_interval = led_update_interval

    self.dots = adafruit_dotstar.DotStar(board.SCK, board.MOSI, 10,
                                         brightness=led_brightness)
    self.dots.fill((0, 0, 255))  # Blue
    self.labjack = self.InitializeLabJack()
    self.tfwriter = None

    self.pusher = timescale.Pusher(live_data=live_data)
    self.session = gps_pb2.Session()
    self.AddNewLap()
    self.point = None
    self.best_lap = None
    self.tree = None
    self.last_led_update = time.time()
    self.speed_deltas = collections.deque(maxlen=speed_deltas)

  def InitializeLabJack(self):
    try:
      return u3.U3()
    except u3.LabJackException:
      logging.exception('Unable to intialize labjack')

  def AddNewLap(self):
    """Adds a new lap to the current session."""
    session = self.session
    lap = session.laps.add()
    self.lap = lap
    self.lap.number = len(session.laps)
    self.pusher.lap_queue.put_nowait(lap)

  def FindNearestBestLapPoint(self):
    """Returns the nearest point on the best lap to the given point."""
    point = self.point
    neighbors = self.tree.query([[point.lat, point.lon]], k=1,
                                return_distance=False)
    for neighbor in neighbors[0]:
      x = self.tree.data[:, 0][neighbor]
      y = self.tree.data[:, 1][neighbor]
      for point_b in self.best_lap.points:
        if point_b.lat == x and point_b.lon == y:
          return point_b

  def LedInterval(self):
    """Returns True if it is safe to update the LEDs based on interval."""
    now = time.time()
    if now - self.last_led_update > self.led_update_interval:
      self.last_led_update = now
      return True
    return False

  def GetLedColor(self):
    median_delta = self.GetMovingSpeedDelta()
    if median_delta > 0:
      return (255, 0, 0)  # Red
    return (0, 255, 0)  # Green

  def GetMovingSpeedDelta(self):
    """Returns the median speed delta over a time period based on the ring size.

    This helps smooth out the LEDs a bit so they're not so flickery by looking
    a moving median of the speed deltas.  Ring size controls how big the ring
    buffer can be, IE the number of deltas to hold on to.  At a GPS singal of
    10hz a ring size of 10 will cover a second worth of time.
    """
    return statistics.median(self.speed_deltas)

  def UpdateSpeedDeltas(self, point, best_point):
    speed_delta = best_point.speed - point.speed
    self.speed_deltas.append(speed_delta)
    return statistics.median(self.speed_deltas)

  def LedPerTenth(self):
    """Dead code but keeping it for at track testing."""
    speed_delta = abs(self.GetMovingSpeedDelta())
    tenths = speed_delta // 0.1
    led_color = self.GetLedColor()
    if not tenths:
      self.dots.fill((0, 0, 0))
    elif speed_delta < 10 and speed_delta < 1:
      leds_to_light = range(int(tenths))
      for led_index in leds_to_light:
        self.dots[led_index] = led_color
      leds_to_off = set(range(len(self.dots))) - set(leds_to_light)
      for led_index in leds_to_off:
        self.dots[led_index] = (0, 0, 0)  # Off
    else:
      self.dots.fill(led_color)

  def UpdateLeds(self):
    """Update LEDs based on speed difference to the best lap."""
    if self.tree and self.LedInterval():
      point = self.point
      best_point = self.FindNearestBestLapPoint()
      self.UpdateSpeedDeltas(point, best_point)
      led_color = self.GetLedColor()
      self.dots.fill(led_color)

  def LogPoint(self):
    point = self.point
    if not self.tfwriter:
      utc_dt = point.time.ToDatetime()
      current_dt = utc_dt.replace(
        tzinfo=datetime.timezone.utc).astimezone(tz=None)
      current_seconds = current_dt.second + current_dt.microsecond / 1e6
      data_filename = os.path.join(
          self.data_log_path, 'data-%s:%03f.tfr' % (
              current_dt.strftime('%Y-%m-%dT%H:%M'), current_seconds))
      logging.info(f'Logging data to {data_filename}')
      self.tfwriter = tf.io.TFRecordWriter(data_filename)
    self.tfwriter.write(point.SerializeToString())

  def ProcessPoint(self):
    """Populates the session with the latest GPS point."""
    point = self.point
    session = self.session
    point.start_finish_distance = PointDelta(point, session.start_finish)
    self.UpdateLeds()
    self.LogPoint()
    self.pusher.point_queue.put_nowait((point, self.lap.number))

  def SetBestLap(self, lap):
    """Sets best lap and builds a KDTree for finding closest points."""
    if (not self.best_lap or
        lap.duration.ToNanoseconds() < self.best_lap.duration.ToNanoseconds()):
      logging.info('New Best Lap')
      self.best_lap = lap
      x_y_points = []
      for point in lap.points:
        x_y_points.append([point.lat, point.lon])
      self.tree = BallTree(np.array(x_y_points), leaf_size=30,
                           metric='pyfunc', func=EarthDistanceSmall)

  def SetLapTime(self):
    """Sets the lap duration based on the first and last point time delta."""
    lap = self.lap
    first_point = lap.points[0]
    last_point = lap.points[-1]
    delta = last_point.time.ToNanoseconds() - first_point.time.ToNanoseconds()
    lap.duration.FromNanoseconds(delta)

    session = self.session
    self.SetBestLap(lap)
    self.pusher.lap_duration_queue.put_nowait((lap.number, lap.duration))

  def CrossStartFinish(self):
    """Checks and handles when the car corsses the start/finish."""
    lap = self.lap
    session = self.session
    if len(lap.points) > self.min_points_per_session:
      point_a = lap.points[-3]
      point_b = lap.points[-2]
      point_c = lap.points[-1]  # Latest point.
      if (point_c.start_finish_distance < self.start_finish_range and
          point_a.start_finish_distance > point_b.start_finish_distance and
          point_c.start_finish_distance > point_b.start_finish_distance):
        logging.info('Start/Finish')
        now = time.time()
        self.last_led_update = now + 1
        self.dots.fill((0, 0, 255))  # Blue
        self.SetLapTime()
        self.AddNewLap()

  def ProcessLap(self):
    """Adds the point to the lap and checks if we crossed start/finish."""
    self.ProcessPoint()
    lap = self.lap
    self.CrossStartFinish()

  def ProcessSession(self):
    """Start/ends the logging of data to log files based on car speed."""
    point = self.point
    session = self.session
    self.ProcessLap()

  def SetTPSVoltage(self, point):
    """Populate TPS voltage if labjack initialzed successfully."""
    if self.labjack:
      try:
        point.voltage = self.labjack.getAIN(0)
      except u3.LabJackException:
        logging.exception('Error reading TPS voltage')

  def PopulatePoint(self, report):
    """Populates the point protocol buffer."""
    session = self.session
    lap = self.lap
    point = lap.points.add()
    point.lat = report.lat
    point.lon = report.lon
    point.alt = report.alt
    point.speed = report.speed
    point.time.FromJsonString(report.time)
    self.SetTPSVoltage(point)
    self.point = point
    if not self.session.track:
      _, track, start_finish = FindClosestTrack(self.point)
      logging.info('Closest track: %s' % track)
      self.session.track = track
      self.session.start_finish.lat = start_finish.lat
      self.session.start_finish.lon = start_finish.lon
      self.pusher.Start(point.time, track)

  def ProcessReport(self, report):
    """Processes a GPS report form the sensor.."""
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      self.PopulatePoint(report)
      self.ProcessSession()

  def Run(self):
    """Runs exit speed in a loop."""
    while True:
      try:
        report = gpsd.next()
        self.ProcessReport(report)
      except Exception as err:
        logging.exception(err, exc_info=True)

if __name__ == '__main__':
  today = datetime.datetime.today()
  filename = 'exit_speed-%s' % today.isoformat()
  logging.basicConfig(filename=os.path.join(DEFAULT_LOG_PATH, filename),
                      level=logging.DEBUG)
  logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
  print(f'Logging to {filename}')
  try:
    while True:
      logging.info('Starting Run')
      es = ExitSpeed()
      es.Run()
  except:  # Catch All!
    logging.exception('Die due to exception', exc_info=True)
  finally:
    logging.info('Done.\nExiting.')
    gpsd.close()
