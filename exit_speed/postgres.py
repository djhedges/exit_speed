#!/usr/bin/python3
# Copyright 2022 Douglas Hedges
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
import datetime
import multiprocessing
import textwrap
from typing import NamedTuple
from typing import Optional
from typing import Text
from typing import Union

import psycopg2
from absl import flags
from absl import logging
from google.protobuf import any_pb2

from exit_speed import common_lib
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

ARGS_ECU = (
  'time',
  'rpm',
  'map_psi',
  'mgp_psi',
  'barometric_pressure_psi',
  'tps',
  'injector_dc',
  'injector_dc_sec',
  'injector_pulse_width',
  'ect_f',
  'iat_f',
  'ecu_volts',
  'maf',
  'gear_position',
  'injector_timing',
  'ignition_timing',
  'lambda_1',
  'trig_1_error_counter',
  'fault_codes',
  'fuel_pressure_psi',
  'oil_temp_f',
  'oil_pressure_psi',
  'knock_level_1',
  'knock_level_2',
  'front_brake_pressure_psi',
  'rear_brake_pressure_psi',
)
PREPARE_ECU = textwrap.dedent("""
  PREPARE ecu_insert AS
  INSERT INTO ecu (
    time,
    rpm,
    map_psi,
    mgp_psi,
    barometric_pressure_psi,
    tps,
    injector_dc,
    injector_dc_sec,
    injector_pulse_width,
    ect_f,
    iat_f,
    ecu_volts,
    maf,
    gear_position,
    injector_timing,
    ignition_timing,
    lambda_1,
    trig_1_error_counter,
    fault_codes,
    fuel_pressure_psi,
    oil_temp_f,
    oil_pressure_psi,
    knock_level_1,
    knock_level_2,
    front_brake_pressure_psi,
    rear_brake_pressure_psi)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26)
""")
INSERT_ECU = textwrap.dedent("""
  EXECUTE ecu_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""")

ARGS_EGTS = (
  'time',
  'egt_1_f',
  'egt_2_f',
  'egt_3_f',
  'egt_4_f',
  'egt_5_f',
  'egt_6_f',
)
PREPARE_EGTS = textwrap.dedent("""
  PREPARE egts_insert AS
  INSERT INTO egts (
    time,
    egt_1_f,
    egt_2_f,
    egt_3_f,
    egt_4_f,
    egt_5_f,
    egt_6_f)
  VALUES ($1, $2, $3, $4, $5, $6, $7)
""")
INSERT_EGTS = textwrap.dedent("""
  EXECUTE egts_insert (%s, %s, %s, %s, %s, %s, %s)
""")

ARGS_PDM = (
  'time',
  'hp_output_1_status',
  'hp_output_1_freq',
  'hp_output_1_duty_cycle',
  'hp_output_1_current',
  'hp_output_2_status',
  'hp_output_2_freq',
  'hp_output_2_duty_cycle',
  'hp_output_2_current',
  'hp_output_3_status',
  'hp_output_3_freq',
  'hp_output_3_duty_cycle',
  'hp_output_3_current',
  'hp_output_4_status',
  'hp_output_4_freq',
  'hp_output_4_duty_cycle',
  'hp_output_4_current',
  'adio_1_status',
  'adio_1_freq',
  'adio_1_duty_cycle',
  'adio_1_voltage',
  'adio_2_status',
  'adio_2_freq',
  'adio_2_duty_cycle',
  'adio_2_voltage',
  'adio_3_status',
  'adio_3_freq',
  'adio_3_duty_cycle',
  'adio_3_voltage',
  'adio_4_status',
  'adio_4_freq',
  'adio_4_duty_cycle',
  'adio_4_voltage',
  'adio_5_status',
  'adio_5_freq',
  'adio_5_duty_cycle',
  'adio_5_voltage',
  'adio_6_status',
  'adio_6_freq',
  'adio_6_duty_cycle',
  'adio_6_voltage',
  'adio_7_status',
  'adio_7_freq',
  'adio_7_duty_cycle',
  'adio_7_voltage',
  'adio_8_status',
  'adio_8_freq',
  'adio_8_duty_cycle',
  'adio_8_voltage',
  'pdm_temp_f',
  'pdm_voltage',
)
PREPARE_PDM = textwrap.dedent("""
  PREPARE pdm_insert AS
  INSERT INTO pdm (
    time,
    hp_output_1_status,
    hp_output_1_freq,
    hp_output_1_duty_cycle,
    hp_output_1_current,
    hp_output_2_status,
    hp_output_2_freq,
    hp_output_2_duty_cycle,
    hp_output_2_current,
    hp_output_3_status,
    hp_output_3_freq,
    hp_output_3_duty_cycle,
    hp_output_3_current,
    hp_output_4_status,
    hp_output_4_freq,
    hp_output_4_duty_cycle,
    hp_output_4_current,
    adio_1_status,
    adio_1_freq,
    adio_1_duty_cycle,
    adio_1_voltage,
    adio_2_status,
    adio_2_freq,
    adio_2_duty_cycle,
    adio_2_voltage,
    adio_3_status,
    adio_3_freq,
    adio_3_duty_cycle,
    adio_3_voltage,
    adio_4_status,
    adio_4_freq,
    adio_4_duty_cycle,
    adio_4_voltage,
    adio_5_status,
    adio_5_freq,
    adio_5_duty_cycle,
    adio_5_voltage,
    adio_6_status,
    adio_6_freq,
    adio_6_duty_cycle,
    adio_6_voltage,
    adio_7_status,
    adio_7_freq,
    adio_7_duty_cycle,
    adio_7_voltage,
    adio_8_status,
    adio_8_freq,
    adio_8_duty_cycle,
    adio_8_voltage,
    pdm_temp_f,
    pdm_voltage)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $40, $41, $42, $43, $44, $45, $46, $47, $48, $49, $50, $51)
""")
INSERT_PDM = textwrap.dedent("""
  EXECUTE pdm_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""")

ARGS_MAP = {
  exit_speed_pb2.Gps: ARGS_GPS,
  exit_speed_pb2.Accelerometer: ARGS_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: ARGS_GYROSCOPE,
  exit_speed_pb2.Labjack: ARGS_LABJACK,
  exit_speed_pb2.WBO2: ARGS_WBO2,
  exit_speed_pb2.Ecu: ARGS_ECU,
  exit_speed_pb2.Egts: ARGS_EGTS,
  exit_speed_pb2.Pdm: ARGS_PDM,
}
PREPARE_MAP = {
  exit_speed_pb2.Gps: PREPARE_GPS,
  exit_speed_pb2.Accelerometer: PREPARE_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: PREPARE_GYROSCOPE,
  exit_speed_pb2.Labjack: PREPARE_LABJACK,
  exit_speed_pb2.WBO2: PREPARE_WBO2,
  exit_speed_pb2.Ecu: PREPARE_ECU,
  exit_speed_pb2.Egts: PREPARE_EGTS,
  exit_speed_pb2.Pdm: PREPARE_PDM,
}
INSERT_MAP = {
  exit_speed_pb2.Gps: INSERT_GPS,
  exit_speed_pb2.Accelerometer: INSERT_ACCELEROMETER,
  exit_speed_pb2.Gyroscope: INSERT_GYROSCOPE,
  exit_speed_pb2.Labjack: INSERT_LABJACK,
  exit_speed_pb2.WBO2: INSERT_WBO2,
  exit_speed_pb2.Ecu: INSERT_ECU,
  exit_speed_pb2.Egts: INSERT_EGTS,
  exit_speed_pb2.Pdm: INSERT_PDM,
}

def ConnectToDB() -> psycopg2.extensions.connection:
  return psycopg2.connect(FLAGS.postgres_db_spec)


def GetConnWithPointPrepare(
  prepare_statement: Text,
  conn: Optional[psycopg2.extensions.connection] =  None,
    ) -> psycopg2.extensions.connection:
  conn = conn or ConnectToDB()
  with conn.cursor() as cursor:
    cursor.execute(prepare_statement)
  return conn


class Postgres(object):
  """Interface for publishing sensor data to Postgres."""

  def __init__(self, proto_class: any_pb2.Any, start_process: bool = True):
    """Initializer."""
    self.proto_class = proto_class
    self._postgres_conn = None
    self._proto_queue = multiprocessing.Queue()
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
    self._postgres_conn = GetConnWithPointPrepare(
            PREPARE_MAP[self.proto_class])
    while not self.stop_process_signal.value:
      self.ExportProto()
      logging.log_every_n_seconds(
        logging.INFO,
        'Postgres: %s point queue size currently at %d.',
        10,
        self.proto_class,
        self._proto_queue.qsize())


SESSION_INSERT = textwrap.dedent("""
INSERT INTO sessions (time, track, car, live_data)
VALUES (%s, %s, %s, %s)
RETURNING id
""")
LAP_INSERT = textwrap.dedent("""
INSERT INTO laps (session_id, number, start_time)
VALUES (%s, %s, %s)
""")
LAP_END_TIME_UPDATE = textwrap.dedent("""
UPDATE laps
SET end_time = %s, duration_ns = %s
WHERE session_id = %s AND number = %s
""")


class LapStart(NamedTuple):
  number: int
  start_time: datetime.datetime


class LapEnd(NamedTuple):
  end_time: datetime.datetime
  duration_ns: int

MAIN_ARG_MAP = {
  LapStart: ('session_id', 'number', 'start_time'),
  LapEnd: ('end_time',),
}


class PostgresWithoutPrepare(object):
  """Interface for publishing session and lap data to Postgres."""

  def __init__(self, start_process: bool = True):
    """Initializer."""
    self.session_id = None
    self.current_lap_number = None
    self._postgres_conn = None
    self._queue = multiprocessing.Queue()
    self.stop_process_signal = multiprocessing.Value('b', False)
    if start_process:
      self.process = multiprocessing.Process(target=self.Loop, daemon=True)
      self.process.start()

  def AddToQueue(self, data: Union[common_lib.Session, LapStart, LapEnd]):
    self._queue.put(data)

  def ExportSession(self, session: common_lib.Session):
    with self._postgres_conn.cursor() as cursor:
      args = (session.time, session.track.name, session.car, session.live_data)
      cursor.execute(SESSION_INSERT, args)
      self.session_id = cursor.fetchone()[0]
      self._postgres_conn.commit()

  def ExportLapStart(self, lap: LapStart):
    with self._postgres_conn.cursor() as cursor:
      args = (self.session_id, lap.number, lap.start_time)
      cursor.execute(LAP_INSERT, args)
      self.current_lap_number = lap.number
      self._postgres_conn.commit()

  def ExportLapEnd(self, lap: LapEnd):
    with self._postgres_conn.cursor() as cursor:
      args = (lap.end_time, lap.duration_ns, self.session_id, self.current_lap_number)
      cursor.execute(LAP_END_TIME_UPDATE, args)
      self._postgres_conn.commit()

  def ExportData(self):
    data = self._queue.get()
    if isinstance(data, common_lib.Session):
      self.ExportSession(data)
    elif isinstance(data, LapStart):
      self.ExportLapStart(data)
    elif isinstance(data, LapEnd):
      self.ExportLapEnd(data)
    else:
      logging.error(
         'Queue has an unknown data type and will be discarded: %s', data)

  def Loop(self):
    """Tries to export data to the postgres backend."""
    self._postgres_conn = ConnectToDB()
    while not self.stop_process_signal.value:
      self.ExportData()
      logging.log_every_n_seconds(
        logging.INFO,
        'Postgres: main data queue size currently at %d.',
        10,
        self._queue.qsize())
