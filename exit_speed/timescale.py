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
"""Timescale interface for exporting data."""
import multiprocessing
import sys
import textwrap
import traceback
from typing import Optional
from typing import Text
from typing import Tuple

import psycopg2
from absl import flags
from absl import logging

from exit_speed import gps_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string('timescale_db_spec',
                    'postgres://exit_speed:faster@localhost:/exit_speed',
                    'Postgres URI connection string.')
flags.DEFINE_integer('commit_cycle', 3,
                     'Number of points to commit at a time.')


SESSION_INSERT = textwrap.dedent("""
INSERT INTO sessions (time, track, car, live_data)
VALUES (%s, %s, %s, %s)
RETURNING id
""")
LAP_INSERT = textwrap.dedent("""
INSERT INTO laps (session_id, number)
VALUES (%s, %s)
RETURNING id
""")
LAP_DURATION_UPDATE = textwrap.dedent("""
UPDATE laps
SET duration_ms = %s
WHERE id = %s
""")
POINT_PREPARE = textwrap.dedent("""
PREPARE point_insert AS
INSERT INTO points (
    time, session_id, lap_id, lat, lon,
    alt, speed, geohash, elapsed_duration_ms, elapsed_distance_m,
    tps_voltage, water_temp_voltage, oil_pressure_voltage, rpm, afr,
    fuel_level_voltage, accelerometer_x, accelerometer_y, accelerometer_z,
    pitch, roll, gyro_x, gyro_y, gyro_z,
    front_brake_pressure_voltage, rear_brake_pressure_voltage,
    battery_voltage, oil_temp_voltage, labjack_temp_f,
    lf_tire_temp_inner, lf_tire_temp_middle, lf_tire_temp_outer,
    rf_tire_temp_inner, rf_tire_temp_middle, rf_tire_temp_outer,
    lr_tire_temp_inner, lr_tire_temp_middle, lr_tire_temp_outer,
    rr_tire_temp_inner, rr_tire_temp_middle, rr_tire_temp_outer
    )
VALUES ($1, $2, $3, $4, $5,
        $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15,
        $16, $17, $18, $19, $20,
        $21, $22, $23, $24, $25,
        $26, $27, $28, $29,
        $30, $31, $32,
        $33, $34, $35,
        $36, $37, $38,
        $39, $40, $41)
""")
POINT_INSERT = textwrap.dedent("""
EXECUTE point_insert (%s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s)
""")


def ConnectToDB() -> psycopg2.extensions.connection:
  return psycopg2.connect(FLAGS.timescale_db_spec)


def GetConnWithPointPrepare(conn: psycopg2.extensions.connection =  None):
  conn = conn or ConnectToDB()
  with conn.cursor() as cursor:
    cursor.execute(POINT_PREPARE)
  return conn


class Timescale(object):
  """Interface for publishing data to timescale."""

  def __init__(self,
      car: Text,
      live_data: bool = True,
      start_process: bool = True):
    self.car = car
    self.live_data = live_data
    if start_process:
      self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    self.stop_process_signal = multiprocessing.Value('b', False)
    self.manager = multiprocessing.Manager()
    self.timescale_conn = None
    self.session_time = None
    self.track = None
    self.session_id = None
    self.lap_number_ids = {}
    self.lap_queue = multiprocessing.Queue()
    self.lap_duration_queue = multiprocessing.Queue()
    self.point_queue = self.manager.list()  # Used as LifoQueue.
    self.retry_point_queue = []
    self.commit_cycle = 0

  def AddPointToQueue(self, point: gps_pb2.Point, lap_number: int):
    self.point_queue.append((point.SerializeToString(), lap_number))

  def ExportSession(self, cursor: psycopg2.extensions.cursor):
    if not self.session_id:
      args = (self.session_time.ToJsonString(), self.track, self.car,
              self.live_data)
      cursor.execute(SESSION_INSERT, args)
      self.session_id = cursor.fetchone()[0]
      self.timescale_conn.commit()

  def ExportLap(self, lap: gps_pb2.Lap, cursor: psycopg2.extensions.cursor):
    """Export the lap data to timescale."""
    args = (self.session_id, lap.number)
    cursor.execute(LAP_INSERT, args)
    self.lap_number_ids[lap.number] = cursor.fetchone()[0]
    self.timescale_conn.commit()

  def UpdateLapDuration(self,
                        lap_number: int,
                        duration: gps_pb2.Lap.duration,
                        cursor: psycopg2.extensions.cursor):
    """Exports lap duration to the Timescale backend."""
    args = (duration.ToMilliseconds(), self.lap_number_ids[lap_number])
    cursor.execute(LAP_DURATION_UPDATE, args)
    self.timescale_conn.commit()

  def ExportPoint(self,
                  point: gps_pb2.Point,
                  lap_number: int,
                  cursor: psycopg2.extensions.cursor):
    """Exports point data to timescale."""
    lap_id = self.lap_number_ids.get(lap_number)
    if lap_id:
      args = (point.time.ToJsonString(),
              self.session_id,
              lap_id,
              point.lat,
              point.lon,
              point.alt,
              point.speed * 2.23694,  # m/s to mph,
              point.geohash,
              point.elapsed_duration_ms,
              point.elapsed_distance_m,
              point.tps_voltage,
              point.water_temp_voltage,
              point.oil_pressure_voltage,
              point.rpm,
              point.afr,
              point.fuel_level_voltage,
              point.accelerometer_x,
              point.accelerometer_y,
              point.accelerometer_z,
              point.pitch,
              point.roll,
              point.gyro_x,
              point.gyro_y,
              point.gyro_z,
              point.front_brake_pressure_voltage,
              point.rear_brake_pressure_voltage,
              point.battery_voltage,
              point.oil_temp_voltage,
              point.labjack_temp_f,
              point.lf_tire_temp.inner,
              point.lf_tire_temp.middle,
              point.lf_tire_temp.outer,
              point.rf_tire_temp.inner,
              point.rf_tire_temp.middle,
              point.rf_tire_temp.outer,
              point.lr_tire_temp.inner,
              point.lr_tire_temp.middle,
              point.lr_tire_temp.outer,
              point.rr_tire_temp.inner,
              point.rr_tire_temp.middle,
              point.rr_tire_temp.outer,
              )
      cursor.execute(POINT_INSERT, args)
    else:
      self.retry_point_queue.append((point, lap_number))

  def GetLapFromQueue(self) -> Optional[gps_pb2.Lap]:
    if self.lap_queue.qsize() > 0:
      return gps_pb2.Lap().FromString(self.lap_queue.get())

  def GetLapDurationFromQueue(self) -> Optional[Tuple[int, int]]:
    if self.lap_duration_queue.qsize() > 0:
      return self.lap_duration_queue.get()

  def GetPointFromQueue(self) -> Optional[Tuple[gps_pb2.Point, int]]:
    """Blocks until a point is ready to export."""
    if self.retry_point_queue and not self.point_queue:
      return self.retry_point_queue.pop()
    # Queue is empty.
    while not self.point_queue:
      if self.stop_process_signal.value:
        return
    serialized_point, lap_number = self.point_queue.pop()
    return gps_pb2.Point().FromString(serialized_point), lap_number

  def _Commit(self):
    """Commits points to timescale based on FLAGS.commit_cycle."""
    if (self.commit_cycle >= FLAGS.commit_cycle or
        self.stop_process_signal.value):
      self.timescale_conn.commit()
      self.commit_cycle = 0
    else:
      self.commit_cycle += 1

  def Do(self):
    """One iteration of the infinite loop."""
    lap = None
    lap_number_und_duration = None
    point = None
    try:
      if not self.timescale_conn:
        self.timescale_conn = GetConnWithPointPrepare()
      lap = self.GetLapFromQueue()
      lap_number_und_duration = self.GetLapDurationFromQueue()
      point_und_lap_number = self.GetPointFromQueue()
      if point_und_lap_number:
        with self.timescale_conn.cursor() as cursor:
          self.ExportSession(cursor)
          if lap:
            self.ExportLap(lap, cursor)
          if lap_number_und_duration:
            self.UpdateLapDuration(lap_number_und_duration[0],
                                   lap_number_und_duration[1],
                                   cursor)
          self.ExportPoint(point_und_lap_number[0],
                           point_und_lap_number[1],
                           cursor)
          self._Commit()
    except psycopg2.Error:
      stack_trace = ''.join(traceback.format_exception(*sys.exc_info()))
      logging.log_every_n_seconds(logging.ERROR,
                                  'Error writing to timescale database\n%s',
                                  10,
                                  stack_trace)
      # Repopulate queues on errors.
      if lap:
        self.lap_queue.put(lap)
      if lap_number_und_duration:
        self.lap_duration_queue.put(lap_number_und_duration)
      if point:
        self.retry_point_queue.append(point_und_lap_number)
      self.timescale_conn = None  # Reset connection

  def Loop(self):
    """Tries to export point data to the timescale backend."""
    while not self.stop_process_signal.value:
      self.Do()
    if self.timescale_conn:
      self.timescale_conn.commit()

  def Start(self, session_time, track):
    self.session_time = session_time
    self.track = track
    self.process.start()
