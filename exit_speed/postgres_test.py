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
"""Unitests for postgres.py"""
import datetime
import unittest

import pytz
from absl.testing import absltest

from exit_speed import common_lib
from exit_speed import exit_speed_pb2
from exit_speed import postgres
from exit_speed import postgres_test_lib
from exit_speed.tracks import test_track


class TestPostgres(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Postgres unittests."""

  def testArgsMapLookup(self):
    self.assertTupleEqual(
            postgres.ARGS_GPS,
            postgres.ARGS_MAP[exit_speed_pb2.Gps])

  def testPrepareMapLookup(self):
    self.assertEqual(
            postgres.PREPARE_GPS,
            postgres.PREPARE_MAP[exit_speed_pb2.Gps])

  def testInsertMapLookup(self):
    self.assertEqual(
            postgres.INSERT_GPS,
            postgres.INSERT_MAP[exit_speed_pb2.Gps])

  def testExportGps(self):
    proto = exit_speed_pb2.Gps(
      lat=23,
      lon=34,
      alt=45,
      speed_ms=86)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Gps, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM gps')
    time, lat, lon, alt, speed_ms = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(23, lat)
    self.assertEqual(34, lon)
    self.assertEqual(45, alt)
    self.assertEqual(86, speed_ms)

  def testExportAccelerometer(self):
    proto = exit_speed_pb2.Accelerometer(
      accelerometer_x = 1.0,
      accelerometer_y = 2.0,
      accelerometer_z = 3.0)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Accelerometer,
                                  start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM accelerometer')
    (time, accelerometer_x,
     accelerometer_y, accelerometer_z) = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(1.0, accelerometer_x)
    self.assertEqual(2.0, accelerometer_y)
    self.assertEqual(3.0, accelerometer_z)

  def testExportGyroscope(self):
    proto = exit_speed_pb2.Gyroscope(
      gyro_x = 1.0,
      gyro_y = 2.0,
      gyro_z = 3.0)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Gyroscope, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM gyroscope')
    time, gyro_x, gyro_y, gyro_z = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(1.0, gyro_x)
    self.assertEqual(2.0, gyro_y)
    self.assertEqual(3.0, gyro_z)

  def testExportLabjack(self):
    proto = exit_speed_pb2.Labjack(
      labjack_temp_f=120,
      battery_voltage=13.5,
      front_brake_pressure_voltage=4.5,
      fuel_level_voltage=8.0,
      fuel_pressure_voltage=3.5,
      oil_pressure_voltage=2.5,
      oil_temp_voltage=3.0,
      rear_brake_pressure_voltage=3.7,
      water_temp_voltage=3.3,
    )
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.Labjack, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM labjack')
    (
      time,
      labjack_temp_f,
      battery_voltage,
      front_brake_pressure_voltage,
      fuel_level_voltage,
      fuel_pressure_voltage,
      oil_pressure_voltage,
      oil_temp_voltage,
      rear_brake_pressure_voltage,
      water_temp_voltage) = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(120, labjack_temp_f)
    self.assertEqual(13.5, battery_voltage)
    self.assertEqual(4.5, front_brake_pressure_voltage)
    self.assertEqual(8.0, fuel_level_voltage)
    self.assertEqual(3.5, fuel_pressure_voltage)
    self.assertEqual(2.5, oil_pressure_voltage)
    self.assertEqual(3.0, oil_temp_voltage)
    self.assertEqual(3.7, rear_brake_pressure_voltage)
    self.assertEqual(3.3, water_temp_voltage)

  def testExportWBO2(self):
    proto = exit_speed_pb2.WBO2(
      afr=13.0,
      rpm=3250,
      tps_voltage=4.5)
    proto.time.FromJsonString(u'2020-05-23T17:47:44.100Z')
    interface = postgres.Postgres(exit_speed_pb2.WBO2, start_process=False)
    interface.AddProtoToQueue(proto)
    interface.ExportProto()
    self.cursor.execute('SELECT * FROM wbo2')
    time, afr, rpm, tps_voltage = self.cursor.fetchone()
    self.assertEqual(
            datetime.datetime(2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC),
            time)
    self.assertEqual(13.0, afr)
    self.assertEqual(3250, rpm)
    self.assertEqual(4.5, tps_voltage)

  def testExportData(self):
    interface = postgres.PostgresWithoutPrepare(start_process=False)
    start_time = datetime.datetime(
        2020, 5, 23, 17, 47, 44, 100000, tzinfo=pytz.UTC)
    session = common_lib.Session(
        time=start_time,
        track=test_track.TestTrack,
        car='RC Car',
        live_data=False)
    interface.AddToQueue(session)
    interface.ExportData()
    self.cursor.execute('SELECT * FROM sessions')
    db_id, db_time, db_track, db_car, db_live_data = self.cursor.fetchone()
    self.assertEqual(db_id, interface.session_id)
    self.assertEqual(db_time, start_time)
    self.assertEqual(db_track, test_track.TestTrack.name)
    self.assertEqual(db_car, 'RC Car')
    self.assertEqual(db_live_data, False)

    lap_start = postgres.LapStart(number=1, start_time=start_time)
    interface.AddToQueue(lap_start)
    interface.ExportData()
    self.cursor.execute('SELECT * FROM laps')
    (_, db_session_id, db_number, db_start_time,
     db_end_time, db_duration_ns) = self.cursor.fetchone()
    self.assertEqual(db_session_id, interface.session_id)
    self.assertEqual(db_number, 1)
    self.assertEqual(db_start_time, start_time)
    self.assertFalse(db_end_time)
    self.assertFalse(db_duration_ns)

    end_time = start_time + datetime.timedelta(seconds=90)
    duration_ns = 71500000000
    lap_end = postgres.LapEnd(end_time=end_time, duration_ns=duration_ns)
    interface.AddToQueue(lap_end)
    interface.ExportData()
    self.cursor.execute('SELECT end_time, duration_ns FROM laps')
    db_end_time, db_duration_ns  = self.cursor.fetchone()
    self.assertEqual(db_end_time, end_time)
    self.assertEqual(db_duration_ns, duration_ns)


if __name__ == '__main__':
  absltest.main()
