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
import datetime
import multiprocessing
import os

import sdnotify
import u3
from absl import app
from absl import logging

from exit_speed import accelerometer
from exit_speed import common_lib
from exit_speed import config_lib
from exit_speed import exit_speed_pb2
from exit_speed import gps_sensor
from exit_speed import gyroscope
from exit_speed import labjack
from exit_speed import lap_lib
from exit_speed import leds
from exit_speed import postgres
from exit_speed import tire_temperature
from exit_speed import tracks
from exit_speed import wbo2


class ExitSpeed(object):
  """Main object which loops and logs data."""
  LABJACK_TIMER_CMD = u3.Timer0(UpdateReset=True, Value=0, Mode=None)
  REPORT_REQ_FIELDS = ('lat', 'lon', 'time', 'speed')

  def __init__(
      self,
      start_finish_range=20,  # Meters, ~4x the width of straightaways.
      live_data=True,
      min_points_per_session=60 * 10):  # 1 min @ gps 10hz):
    """Initializer.

    Args:
      start_finish_range: Maximum distance a point can be considered when
                          determining if the car crosses the start/finish.
      live_data: A boolean, if True indicates that this session's data should be
                 tagged as live.
      min_points_per_session:  Used to prevent sessions from prematurely ending.
    """
    self.start_finish_range = start_finish_range
    self.live_data = live_data
    self.min_points_per_session = min_points_per_session
    self.point_queue = multiprocessing.Queue()

    self.config = config_lib.LoadConfig()
    self.leds = leds.LEDs()
    self.postgres = None
    self.track = None
    self.lap_number = 0
    self.laps = {}
    self.current_lap = []
    self.point = None
    self.sdnotify = sdnotify.SystemdNotifier()
    self.sdnotify.notify('READY=1')

  def InitializeSubProcesses(self):
    """Initialize subprocess modules based on config.yaml."""
    if self.config.get('postgres'):
      self.postgres = postgres.PostgresWithoutPrepare()
    if self.config.get('gps'):
      self.gps = gps_sensor.GPSProcess(self.config, self.point_queue)
      while self.point_queue.empty():
        self.point = exit_speed_pb2.Gps().FromString(self.point_queue.get())
        logging.log_every_n_seconds(
            logging.INFO,
            'Waiting for GPS fix to determine track before starting other '
            'sensor subprocesses',
            10)
        break
    self.ProcessSession()
    if self.config.get('accelerometer'):
      self.accel = accelerometer.AccelerometerProcess(
          self.config, self.point_queue)
    if self.config.get('gyroscope'):
      self.gyro = gyroscope.GyroscopeProcess(self.config, self.point_queue)
    if self.config.get('labjack'):
      self.labjack = labjack.Labjack(self.config, self.point_queue)
    if self.config.get('tire_temps'):
      self.tire_temps = tire_temperature.MultiTireInterface(
          self.config, self.point_queue)
    if self.config.get('wbo2'):
      self.wbo2 = wbo2.WBO2(self.config, self.point_queue)

  def AddNewLap(self) -> None:
    """Adds a new lap to the current session."""
    self.lap_number += 1
    self.current_lap = []
    self.laps[self.lap_number] = self.current_lap
    if self.config.get('postgres'):
      self.postgres.AddToQueue(
          postgres.LapStart(number=self.lap_number,
														start_time=self.point.time))

  def ProcessPoint(self) -> None:
    """Updates LEDs, logs point and writes data to PostgresSQL."""
    point = self.point
    self.leds.UpdateLeds(point)

  def SetLapTime(self) -> None:
    """Sets the lap duration based on the first and last point time delta."""
    duration_ns = lap_lib.CalcLastLapDuration(self.track, self.session)
    self.leds.SetBestLap(self.lap, delta)
    minutes = duration_ns / 1e9 // 60
    seconds = (duration_ns / 1e6 % 60000) / 1000.0
    logging.info('New Lap %d:%.03f', minutes, seconds)
    if self.config.get('postgres'):
      self.postgres.AddToQueue(postgres.LapEnd(end_time=self.point.time))

  def CrossStartFinish(self) -> None:
    """Checks and handles when the car crosses the start/finish."""
    if len(self.current_lap) >= self.min_points_per_session:
      prior_point = lap_lib.GetPriorUniquePoint(self.lap, self.point)
      if (self.point.start_finish_distance < self.start_finish_range and
          # First point past start/finish has an obtuse angle.
          lap_lib.SolvePointBAngle(self.track, prior_point, self.point) > 90):
        logging.info('Start/Finish')
        self.leds.CrossStartFinish()
        self.SetLapTime()
        self.AddNewLap()
        # Start and end laps on the same point just past start/finish.
        self.lap.append(prior_point)
    self.current_lap.append(self.point)

  def ProcessLap(self) -> None:
    """Adds the point to the lap and checks if we crossed start/finish."""
    self.ProcessPoint()
    self.CrossStartFinish()

  def ProcessSession(self) -> None:
    """Populates the session proto."""
    _, track, start_finish = tracks.FindClosestTrack(self.point)
    self.track = track
    logging.info('Closest track: %s', track.name)
    if self.config.get('postgres'):
      self.postgres.AddToQueue(postgres.Session(
        track=track,
        car=self.config['car'],
        live_data=self.live_data))

  def Run(self) -> None:
    """Runs exit speed in a loop."""
    self.InitializeSubProcesses()
    self.AddNewLap()
    while True:
      self.point = exit_speed_pb2.Gps().FromString(self.point_queue.get())
      self.ProcessLap()
      logging.log_every_n_seconds(
          logging.INFO,
          'Main: Point queue size currently at %d.',
          10,
          self.point_queue.qsize())
      self.sdnotify.notify(
          'STATUS=Last report time:%s' % self.point.time.ToJsonString())
      self.sdnotify.notify('WATCHDOG=1')


def main(unused_argv) -> None:
  logging.get_absl_handler().use_absl_log_file()
  es = None
  try:
    while True:
      logging.info('Starting Run')
      es = ExitSpeed()
      es.Run()
  except KeyboardInterrupt:
    logging.info('Keyboard interrupt')
  finally:
    if hasattr(es, 'point'):
      logging.info('Logging last point\n %s', es.point)
    logging.info('Done.\nExiting.')
    logging.exception('Ensure we log any exceptions')


if __name__ == '__main__':
  app.run(main)
