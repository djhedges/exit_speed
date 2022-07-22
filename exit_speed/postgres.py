#!/usr/bin/python3
# Copyright 2022 Google LLC
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
"""Postgres interface."""

from typing import Text
import multiprocessing
import textwrap
import psycopg2
from absl import flags
from absl import logging
from google.protobuf import any_pb2
from exit_speed import exit_speed_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string('postgres_db_spec',
                    'postgres://exit_speed:faster@localhost:/exit_speed',
                    'Postgres URI connection string.')

ARGS_GPS = ('time', 'lat', 'lon', 'alt', 'speed_ms')
PREPARE_GPS = textwrap.dedent("""
  PREPARE gps_insert AS
  INSERT INTO gps (time, lat, lon, alt, speed_ms)
  VALUES ($1, $2, $3, $4, $5)
""")
INSERT_GPS = textwrap.dedent("""
  EXECUTE gps_insert (%s, %s, %s, %s, %s)
""")

ARGS_ACCELEROMETER = (
  'time', 'accelerometer_x', 'accelerometer_y', 'accelerometer_z')
PREPARE_ACCELEROMETER = textwrap.dedent("""
  PREPARE accelerometer_insert AS
  INSERT INTO accelerometer (
    time, accelerometer_x, accelerometer_y, accelerometer_z)
  VALUES ($1, $2, $3, $4)
""")
INSERT_ACCELEROMETER = textwrap.dedent("""
  EXECUTE accelerometer_insert (%s, %s, %s, %s)
""")

ARGS_GYROSCOPE = (
  'time', 'gyro_x', 'gyro_y', 'gyro_z')
PREPARE_GYROSCOPE = textwrap.dedent("""
  PREPARE gyroscope_insert AS
  INSERT INTO gyroscope (time, gyro_x, gyro_y, gyro_z)
  VALUES ($1, $2, $3, $4)
""")
INSERT_GYROSCOPE = textwrap.dedent("""
  EXECUTE gyroscope_insert (%s, %s, %s, %s)
""")

ARGS_LABJACK = (
  'time',
  'labjack_temp_f',
  'battery_voltage',
  'front_brake_pressure_voltage',
  'fuel_level_voltage',
  'fuel_pressure_voltage',
  'oil_pressure_voltage',
  'oil_temp_voltage',
  'rear_brake_pressure_voltage',
  'water_temp_voltage',
)
PREPARE_LABJACK = textwrap.dedent("""
  PREPARE labjack_insert AS
  INSERT INTO labjack (
    time,
    labjack_temp_f,
    battery_voltage,
    front_brake_pressure_voltage,
    fuel_level_voltage,
    fuel_pressure_voltage,
    oil_pressure_voltage,
    oil_temp_voltage,
    rear_brake_pressure_voltage,
    water_temp_voltage)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
""")
INSERT_LABJACK = textwrap.dedent("""
  EXECUTE labjack_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""")

ARGS_WBO2 = (
  'time', 'afr', 'rpm', 'tps_voltage')
PREPARE_WBO2 = textwrap.dedent("""
  PREPARE wbo2_insert AS
  INSERT INTO wbo2 (time, afr, rpm, tps_voltage)
  VALUES ($1, $2, $3, $4)
""")
INSERT_WBO2 = textwrap.dedent("""
  EXECUTE wbo2_insert (%s, %s, %s, %s)
""")

ARGS_MAP = {
  exit_speed_pb2.Gps: ARGS_GPS,
  exit_speed_pb2.Accelerometer: ARGS_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: ARGS_GYROSCOPE,
  exit_speed_pb2.Labjack: ARGS_LABJACK,
  exit_speed_pb2.WBO2: ARGS_WBO2,
}
PREPARE_MAP = {
  exit_speed_pb2.Gps: PREPARE_GPS,
  exit_speed_pb2.Accelerometer: PREPARE_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: PREPARE_GYROSCOPE,
  exit_speed_pb2.Labjack: PREPARE_LABJACK,
  exit_speed_pb2.WBO2: PREPARE_WBO2,
}
INSERT_MAP = {
  exit_speed_pb2.Gps: INSERT_GPS,
  exit_speed_pb2.Accelerometer: INSERT_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: INSERT_GYROSCOPE,
  exit_speed_pb2.Labjack: INSERT_LABJACK,
  exit_speed_pb2.WBO2: INSERT_WBO2,
}


def ConnectToDB() -> psycopg2.extensions.connection:
  return psycopg2.connect(FLAGS.postgres_db_spec)


def GetConnWithPointPrepare(
  prepare_statement: Text, conn: psycopg2.extensions.connection =  None):
  conn = conn or ConnectToDB()
  with conn.cursor() as cursor:
    cursor.execute(prepare_statement)
  return conn


class Postgres(object):
  """Interface for publishing data to Postgres."""

  def __init__(self, proto_class: any_pb2.Any, start_process: bool = True):
    """Initializer."""
    self.proto_class = proto_class
    self._postgres_conn = GetConnWithPointPrepare(
            PREPARE_MAP[proto_class])
    self._proto_queue = multiprocessing.Queue()  # Used as LifoQueue.
    self.stop_process_signal = multiprocessing.Value('b', False)
    if start_process:
      self.process = multiprocessing.Process(target=self.Loop, daemon=True)
      self.process.start()

  def AddProtoToQueue(self, proto: any_pb2.Any):
    self._proto_queue.put(proto.SerializeToString())

  def ExportProto(self):
    proto = self.proto_class().FromString(self._proto_queue.get())
    args = []
    for value in ARGS_MAP[self.proto_class]:
      if value == 'time':
        args.append(proto.time.ToJsonString())
      else:
        args.append(getattr(proto, value))
    with self._postgres_conn.cursor() as cursor:
      cursor.execute(INSERT_MAP[self.proto_class], args)
      self._postgres_conn.commit()

  def Loop(self):
    """Tries to export data to the postgres backend."""
    while not self.stop_process_signal.value:
      self.ExportProto()
      logging.log_every_n_seconds(
        logging.INFO,
        'Postgres: %s point queue size currently at %d.',
        10,
        self.proto_class,
        self._proto_queue.qsize())
