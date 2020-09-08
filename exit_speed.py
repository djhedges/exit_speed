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
"""The main script for starting exit speed."""

import collections
import datetime
import os
import statistics
from typing import Text
from typing import Tuple
from absl import app
from absl import flags
from absl import logging
from gps import client
from gps import EarthDistanceSmall
from gps import gps
from gps import WATCH_ENABLE
from gps import WATCH_NEWSTYLE
import gps_pb2
import labjack
import leds
import numpy as np
from sklearn.neighbors import BallTree
import tensorflow as tf
import timescale
import u3
import wbo2

FLAGS = flags.FLAGS

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

TRACKS = {(45.695079, -121.525848): 'Test Parking Lot',
          (45.363799, -120.744556): 'Oregon Raceway Park',
          (45.595015, -122.694526): 'Portland International Raceway',
          (47.254702, -123.192676): 'The Ridge Motorsport Park',
          (47.321082, -122.149664): 'Pacific Raceway',
          (47.661806, -117.572297): 'Spokane Raceway'}

DEFAULT_LOG_PATH = '/home/pi/lap_logs'


def PointDelta(point_a: gps_pb2.Point, point_b: gps_pb2.Point) -> float:
  """Returns the distance between two points."""
  return EarthDistanceSmall((point_a.lat, point_a.lon),
                            (point_b.lat, point_b.lon))


def FindClosestTrack(
    point: gps_pb2.Point) -> Tuple[float, Text, gps_pb2.Point]:
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
  LABJACK_TIMER_CMD = u3.Timer0(UpdateReset=True, Value=0, Mode=None)

  def __init__(
      self,
      data_log_path=DEFAULT_LOG_PATH,
      start_finish_range=10,  # Meters, ~2x the width of straightaways.
      min_points_per_session=60 * 10,  # 1 min @ gps 10hz
      speed_deltas=50,
      live_data=True):
    """Initializer.

    Args:
      data_log_path: Path to log the point data.
      start_finish_range: Maximum distance a point can be considered when
                          determining if the car crosses the start/finish.
      min_points_per_session:  Used to prevent sessions from prematurely ending.
      speed_deltas:  Used to smooth out GPS data.  This controls how many recent
                     speed deltas are stored.  50 at 10hz means a median of the
                     last 5 seconds is used.
      live_data: A boolean, if True indicates that this session's data should be
                 tagged as live.
    """
    self.data_log_path = data_log_path
    self.start_finish_range = start_finish_range
    self.min_points_per_session = min_points_per_session
    self.leds = leds.LEDs()

    self.labjack = labjack.Labjack()
    self.wide_band = wbo2.WBO2()
    self.tfwriter = None

    self.pusher = timescale.Pusher(live_data=live_data)
    self.session = gps_pb2.Session()
    self.AddNewLap()
    self.point = None
    self.best_lap = None
    self.tree = None
    self.speed_deltas = collections.deque(maxlen=speed_deltas)

  def AddNewLap(self) -> None:
    """Adds a new lap to the current session."""
    session = self.session
    lap = session.laps.add()
    self.lap = lap
    self.lap.number = len(session.laps)
    self.pusher.lap_queue.put_nowait(lap)

  def FindNearestBestLapPoint(self) -> gps_pb2.Point:
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

  def GetLedColor(self) -> Tuple[int, int, int]:
    median_delta = self.GetMovingSpeedDelta()
    if median_delta > 0:
      return (255, 0, 0)  # Red
    return (0, 255, 0)  # Green

  def GetMovingSpeedDelta(self) -> float:
    """Returns the median speed delta over a time period based on the ring size.

    This helps smooth out the LEDs a bit so they're not so flickery by looking
    a moving median of the speed deltas.  Ring size controls how big the ring
    buffer can be, IE the number of deltas to hold on to.  At a GPS singal of
    10hz a ring size of 10 will cover a second worth of time.
    """
    return statistics.median(self.speed_deltas)

  def UpdateSpeedDeltas(self,
                        point: gps_pb2.Point,
                        best_point: gps_pb2.Point) -> float:
    speed_delta = best_point.speed - point.speed
    self.speed_deltas.append(speed_delta)
    return statistics.median(self.speed_deltas)

  def UpdateLeds(self) -> None:
    """Update LEDs based on speed difference to the best lap."""
    if self.tree and self.LedInterval():
      point = self.point
      best_point = self.FindNearestBestLapPoint()
      self.UpdateSpeedDeltas(point, best_point)
      led_color = self.GetLedColor()
      self.leds.Fill(led_color)

  def LogPoint(self) -> None:
    """Writes the current point to the data log."""
    point = self.point
    if not self.tfwriter:
      utc_dt = point.time.ToDatetime()
      current_dt = utc_dt.replace(
          tzinfo=datetime.timezone.utc).astimezone(tz=None)
      current_seconds = current_dt.second + current_dt.microsecond / 1e6
      data_filename = os.path.join(
          self.data_log_path, 'data-%s:%03f.tfr' % (
              current_dt.strftime('%Y-%m-%dT%H:%M'), current_seconds))
      logging.info('Logging data to %s', data_filename)
      self.tfwriter = tf.io.TFRecordWriter(data_filename)
    self.tfwriter.write(point.SerializeToString())

  def ProcessPoint(self) -> None:
    """Populates the session with the latest GPS point."""
    point = self.point
    session = self.session
    point.start_finish_distance = PointDelta(point, session.start_finish)
    self.UpdateLeds()
    self.LogPoint()
    self.pusher.point_queue.put_nowait((point, self.lap.number))

  def SetBestLap(self, lap: gps_pb2.Lap) -> None:
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

  def SetLapTime(self) -> None:
    """Sets the lap duration based on the first and last point time delta."""
    lap = self.lap
    first_point = lap.points[0]
    last_point = lap.points[-1]
    delta = last_point.time.ToNanoseconds() - first_point.time.ToNanoseconds()
    lap.duration.FromNanoseconds(delta)
    self.SetBestLap(lap)
    self.pusher.lap_duration_queue.put_nowait((lap.number, lap.duration))

  def CrossStartFinish(self) -> None:
    """Checks and handles when the car corsses the start/finish."""
    lap = self.lap
    if len(lap.points) > self.min_points_per_session:
      point_a = lap.points[-3]
      point_b = lap.points[-2]
      point_c = lap.points[-1]  # Latest point.
      if (point_c.start_finish_distance < self.start_finish_range and
          point_a.start_finish_distance > point_b.start_finish_distance and
          point_c.start_finish_distance > point_b.start_finish_distance):
        logging.info('Start/Finish')
        self.leds.Fill((0, 0, 255),  # Blue
                       additional_delay=1,
                       ignore_update_interval=True)
        self.SetLapTime()
        self.AddNewLap()

  def ProcessLap(self) -> None:
    """Adds the point to the lap and checks if we crossed start/finish."""
    self.ProcessPoint()
    self.CrossStartFinish()

  def ProcessSession(self) -> None:
    """Start/ends the logging of data to log files based on car speed."""
    self.ProcessLap()

  def ReadLabjackValues(self, point: gps_pb2.Point) -> None:
    """Populate voltage readings if labjack initialzed successfully."""
    point.water_temp_voltage = self.labjack.water_temp_voltage.value
    point.oil_pressure_voltage = self.labjack.oil_pressure_voltage.value

  def ReadWideBandValues(self, point) -> None:
    """Populate wide band readings."""
    point.tps_voltage = self.wide_band.tps_voltage.value
    point.afr = self.wide_band.afr.value
    point.rpm = self.wide_band.rpm.value

  def PopulatePoint(self, report: client.dictwrapper) -> None:
    """Populates the point protocol buffer."""
    lap = self.lap
    point = lap.points.add()
    point.lat = report.lat
    point.lon = report.lon
    point.alt = report.alt
    point.speed = report.speed
    point.time.FromJsonString(report.time)
    self.ReadLabjackValues(point)
    self.ReadWideBandValues(point)
    self.point = point
    if not self.session.track:
      _, track, start_finish = FindClosestTrack(self.point)
      logging.info('Closest track: %s', track)
      self.session.track = track
      self.session.start_finish.lat = start_finish.lat
      self.session.start_finish.lon = start_finish.lon
      self.pusher.Start(point.time, track)

  def ProcessReport(self, report: client.dictwrapper) -> None:
    """Processes a GPS report form the sensor.."""
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      self.PopulatePoint(report)
      self.ProcessSession()

  def Run(self) -> None:
    """Runs exit speed in a loop."""
    while True:
      report = gpsd.next()
      self.ProcessReport(report)


def main(unused_argv) -> None:
  logging.get_absl_handler().use_absl_log_file()
  try:
    while True:
      logging.info('Starting Run')
      es = ExitSpeed()
      es.Run()
  except KeyboardInterrupt:
    logging.info('Keyboard interrupt')
  finally:
    logging.info('Done.\nExiting.')
    gpsd.close()


if __name__ == '__main__':
  app.run(main)
