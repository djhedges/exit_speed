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
import os

import accelerometer
import common_lib
import config_lib
import data_logger
import geohash
import gps
import gps_pb2
import gyroscope
import labjack
import lap_lib
import leds
import sdnotify
import timescale
import tire_temperature
import tracks
import u3
import wbo2
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS
flags.DEFINE_string('data_log_path', '/home/pi/lap_logs',
                    'The directory to save data and logs.')


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
    self.last_gps_report = None
    self.min_points_per_session = min_points_per_session

    self.InitializeSubProcesses()
    self.gpsd = gps.gps(mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)
    self.leds = leds.LEDs()
    self.data_logger = None
    self.session = gps_pb2.Session()
    self.AddNewLap()
    self.point = None
    self.sdnotify = sdnotify.SystemdNotifier()
    self.sdnotify.notify('READY=1')

  def InitializeSubProcesses(self):
    """Initialize subprocess modules based on config.yaml."""
    self.config = config_lib.LoadConfig()
    if self.config.get('accelerometer'):
      self.accel = accelerometer.Accelerometer()
    if self.config.get('gyroscope'):
      self.gyro = gyroscope.Gyroscope()
    if self.config.get('labjack'):
      self.labjack = labjack.Labjack(self.config)
    if self.config.get('tire_temps'):
      self.tire_temps = tire_temperature.MultiTireInterface(self.config)
    if self.config.get('wbo2'):
      self.wbo2 = wbo2.WBO2(self.config)
    if self.config.get('timescale'):
      car = self.config['car']
      logging.info('Logging for car: %s', car)
      self.timescale = timescale.Timescale(car, live_data=self.live_data)

  def AddNewLap(self) -> None:
    """Adds a new lap to the current session."""
    session = self.session
    lap = session.laps.add()
    self.lap = lap
    self.lap.number = len(session.laps)
    self.timescale.lap_queue.put(lap)

  def GetLogFilePrefix(self, point: gps_pb2.Point, tz=None):
    utc_dt = point.time.ToDatetime()
    current_dt = utc_dt.replace(
        tzinfo=datetime.timezone.utc).astimezone(tz=tz)
    current_seconds = current_dt.second + current_dt.microsecond / 1e6
    return os.path.join(
        FLAGS.data_log_path,
        '%s/' % self.config.get('car', 'unknown_car'),
        '%s:%03f' % (current_dt.strftime('%Y-%m-%dT%H:%M'), current_seconds))

  def _InitializeDataLogger(self, point: gps_pb2.Point):
    file_prefix = self.GetLogFilePrefix(point)
    logging.info('Logging data to %s', file_prefix)
    self.data_logger = data_logger.Logger(file_prefix)

  def LogPoint(self) -> None:
    """Writes the current point to the data log."""
    point = self.point
    if not self.data_logger:
      self._InitializeDataLogger(point)
    self.data_logger.WriteProto(point)

  def CalculateElapsedValues(self):
    """Populates the elapsed_duration_ms and elapsed_distance_m point values."""
    point = self.point
    if len(self.lap.points) > 1:
      prior_point = lap_lib.GetPriorUniquePoint(self.lap, self.point)
      point.elapsed_duration_ms = (
          point.time.ToMilliseconds() -
          prior_point.time.ToMilliseconds() +
          prior_point.elapsed_duration_ms)
      point.elapsed_distance_m = (
          common_lib.PointDelta(point, prior_point) +
          prior_point.elapsed_distance_m)
    else:
      point.elapsed_duration_ms = 0
      point.elapsed_distance_m = 0

  def ProcessPoint(self) -> None:
    """Calculate values after PopulatePoint is called.

    The key distinction between ProcessPoint and PopulatePoint is that
    ProcessPoint is executed when data is replayed and synced to timescale.
    Where as PopulatePoint is never called again.
    """
    point = self.point
    point.start_finish_distance = common_lib.PointDelta(
        point, self.session.start_finish)
    self.leds.UpdateLeds(point)
    self.CalculateElapsedValues()
    self.LogPoint()
    self.timescale.AddPointToQueue(point, self.lap.number)

  def SetLapTime(self) -> None:
    """Sets the lap duration based on the first and last point time delta."""
    delta = lap_lib.CalcLastLapDuration(self.session)
    self.lap.duration.FromNanoseconds(delta)
    self.leds.SetBestLap(self.lap)
    self.timescale.lap_duration_queue.put((self.lap.number, self.lap.duration))
    minutes = self.lap.duration.ToSeconds() // 60
    seconds = (self.lap.duration.ToMilliseconds() % 60000) / 1000.0
    logging.info('New Lap %d:%.03f', minutes, seconds)

  def CrossStartFinish(self) -> None:
    """Checks and handles when the car crosses the start/finish."""
    if len(self.lap.points) >= self.min_points_per_session:
      prior_point = lap_lib.GetPriorUniquePoint(self.lap, self.point)
      if (self.point.start_finish_distance < self.start_finish_range and
          # First point past start/finish has an obtuse angle.
          lap_lib.SolvePointBAngle(prior_point, self.point) > 90):
        logging.info('Start/Finish')
        self.leds.CrossStartFinish()
        self.SetLapTime()
        self.AddNewLap()
        # Start and end laps on the same point just past start/finish.
        self.lap.points.append(prior_point)
        self.timescale.AddPointToQueue(prior_point, self.lap.number)
        # Reset elapsed values for first point of the lap.
        self.point.elapsed_duration_ms = 0
        self.point.elapsed_distance_m = 0
    self.lap.points.append(self.point)

  def ProcessLap(self) -> None:
    """Adds the point to the lap and checks if we crossed start/finish."""
    self.ProcessPoint()
    self.CrossStartFinish()

  def ProcessSession(self) -> None:
    """Start/ends the logging of data to log files."""
    if not self.session.track:
      _, track, start_finish = tracks.FindClosestTrack(self.point)
      logging.info('Closest track: %s', track.name)
      self.session.track = track.name
      self.session.start_finish.lat = start_finish.lat
      self.session.start_finish.lon = start_finish.lon
      self.timescale.Start(self.point.time, track.name)
    self.ProcessLap()

  def ReadAccelerometerValues(self, point: gps_pb2.Point):
    """Populates the accelerometer values."""
    if self.config.get('accelerometer'):
      x, y, z = self.accel.GetGForces()
      point.accelerometer_x = x
      point.accelerometer_y = y
      point.accelerometer_z = z
      pitch, roll = self.accel.CalcPitchAndRoll(x, y, z)
      point.pitch = pitch
      point.roll = roll

  def ReadGyroscopeValues(self, point: gps_pb2.Point):
    """Populates the gyroscope values."""
    if self.config.get('gyroscope'):
      x, y, z = self.gyro.GetRotationalValues()
      point.gyro_x = x
      point.gyro_y = y
      point.gyro_z = z

  def ReadLabjackValues(self, point: gps_pb2.Point) -> None:
    """Populate voltage readings if labjack initialzed successfully."""
    if self.config.get('labjack'):
      point.labjack_temp_f = self.labjack.labjack_temp_f.value
      for point_value, voltage in self.labjack.voltage_values.items():
        setattr(point, point_value, voltage.value)

  def ReadTireTemperatures(self, point: gps_pb2.Point) -> None:
    """Populate tire temperature readings."""
    if self.config.get('tire_temps'):
      for corner, server in self.tire_temps.servers.items():
        tire_temp = getattr(point, '%s_tire_temp' % corner)
        tire_temp.inner = server.inside_temp_f.value
        tire_temp.middle = server.middle_temp_f.value
        tire_temp.outer = server.outside_temp_f.value

  def ReadWBO2Values(self, point) -> None:
    """Populate wide band readings."""
    if self.config.get('wbo2'):
      for point_value, value in self.wbo2.values.items():
        setattr(point, point_value, value.value)

  def PopulatePoint(self, report: gps.client.dictwrapper) -> None:
    """Populates the point protocol buffer."""
    point = gps_pb2.Point()
    point.lat = report.lat
    point.lon = report.lon
    if report.get('alt'):
      point.alt = report.alt
    point.speed = report.speed
    point.time.FromJsonString(report.time)
    point.geohash = geohash.encode(point.lat, point.lon)
    self.ReadAccelerometerValues(point)
    self.ReadGyroscopeValues(point)
    self.ReadLabjackValues(point)
    self.ReadTireTemperatures(point)
    self.ReadWBO2Values(point)
    self.point = point

  def CheckReportFields(self, report: gps.client.dictwrapper) -> bool:
    """Verifies required report fields are present."""
    for field in self.REPORT_REQ_FIELDS:
      if not report.get(field):
        return False
    return True

  def ProcessReport(self, report: gps.client.dictwrapper) -> None:
    """Processes a GPS report form the sensor.."""
    if (report.get('class') == 'TPV' and self.CheckReportFields(report)):
      if (not self.last_gps_report or
          self.last_gps_report != report.time):
        self.PopulatePoint(report)
        self.ProcessSession()
        self.last_gps_report = report.time
        self.sdnotify.notify('STATUS=Last report time:%s' % report.time)
        self.sdnotify.notify('WATCHDOG=1')

  def Run(self) -> None:
    """Runs exit speed in a loop."""
    while True:
      report = self.gpsd.next()  # pylint: disable=not-callable
      self.ProcessReport(report)


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
    if es:
      es.gpsd.close()


if __name__ == '__main__':
  app.run(main)