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
"""Unitests for timescale.py"""
import os
import unittest

import mock
import psycopg2
import testing.postgresql
from absl.testing import absltest

from exit_speed import gps_pb2
from exit_speed import timescale

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
  Postgresql.clear_cache()


class TestTimescale(unittest.TestCase):
  """Timescale unittest."""

  def setUp(self):
    self.postgresql = Postgresql()
    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'testdata/timescale_schema')
    with open(schema_path) as schema_file:
      statements = ''.join(schema_file.readlines())
    conn = psycopg2.connect(**self.postgresql.dsn())
    cursor = conn.cursor()
    cursor.execute(statements)
    conn.commit()
    self.conn = timescale.GetConnWithPointPrepare(conn)
    self.cursor = self.conn.cursor()
    point = gps_pb2.Point()
    point.time.FromJsonString('2020-09-13T01:36:38.600Z')
    self.pusher = timescale.Timescale(
        'Corrado',
        start_process=False,
        )
    self.pusher.timescale_conn = self.conn
    self.pusher.track = 'Test Parking Lot'
    self.pusher.session_time = point.time

  def tearDown(self):
    self.cursor.close()
    self.conn.close()
    self.postgresql.stop()

  def testExportSession(self):
    self.pusher.ExportSession(self.cursor)
    self.assertEqual(1, self.pusher.session_id)

  def testExportLap(self):
    lap = gps_pb2.Lap()
    lap.number = 1
    self.pusher.ExportLap(lap, self.cursor)
    self.assertDictEqual({1: 1}, self.pusher.lap_number_ids)

  def testUpdateLapDuration(self):
    lap = gps_pb2.Lap()
    lap.duration.FromMilliseconds(90 * 1000)
    lap.number = 1
    self.pusher.ExportSession(self.cursor)
    self.pusher.ExportLap(lap, self.cursor)
    self.pusher.UpdateLapDuration(lap.number, lap.duration, self.cursor)
    self.cursor.execute('SELECT * FROM laps')
    self.conn.commit()
    lap_id, session_id, number, duration_ms = self.cursor.fetchone()
    self.assertEqual(1, lap_id)
    self.assertEqual(1, session_id)
    self.assertEqual(1, number)
    self.assertEqual(90000, duration_ms)

  def testExportPoint(self):
    lap = gps_pb2.Lap()
    lap.duration.FromMilliseconds(90 * 1000)
    lap.number = 1
    self.pusher.ExportSession(self.cursor)
    self.pusher.ExportLap(lap, self.cursor)
    self.pusher.UpdateLapDuration(lap.number, lap.duration, self.cursor)

    point = lap.points.add()
    point.alt = 1
    point.speed = 1
    point.lat = 45.69545832462609
    point.lon = -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    point.accelerometer_x = 0.0
    point.accelerometer_y = 1.7
    point.accelerometer_z = 1.2
    point.pitch = 0.2
    point.roll = 5.0
    point.gyro_x = 0.0
    point.gyro_y = 1.0
    point.gyro_z = 2.5
    point.geohash = 'c21efweg66fd'
    point.elapsed_duration_ms = 10
    point.elapsed_distance_m = 33
    point.front_brake_pressure_voltage = 3.5
    point.rear_brake_pressure_voltage = 2.5
    point.battery_voltage = 13.5
    point.oil_temp_voltage = 2.5
    point.labjack_temp_f = 77.9
    point.lf_tire_temp.inner = 170.0
    point.lf_tire_temp.middle = 180.0
    point.lf_tire_temp.outer = 200.0
    point.rf_tire_temp.inner = 190.0
    point.rf_tire_temp.middle = 190.0
    point.rf_tire_temp.outer = 190.0
    self.pusher.ExportPoint(point, 1, self.cursor)
    self.cursor.execute('SELECT * FROM points')
    (_, _, _, lat, lon, alt, speed, geohash, elapsed_duration_ms,
     elapsed_distance_m, tps_voltage, water_temp_voltage, oil_pressure_voltage,
     rpm, afr, fuel_level_voltage, accelerometer_x, accelerometer_y,
     accelerometer_z, pitch, roll, gyro_x, gyro_y, gyro_z,
     front_brake_pressure_voltage, rear_brake_pressure_voltage,
     battery_voltage, oil_temp_voltage, labjack_temp_f,
     lf_tire_temp_inner, lf_tire_temp_middle, lf_tire_temp_outer,
     rf_tire_temp_inner, rf_tire_temp_middle, rf_tire_temp_outer,
     lr_tire_temp_inner, lr_tire_temp_middle, lr_tire_temp_outer,
     rr_tire_temp_inner, rr_tire_temp_middle, rr_tire_temp_outer
     ) = self.cursor.fetchone()
    self.assertEqual(lat, 45.6954583246261)
    self.assertEqual(lon, -121.525511797518)
    self.assertEqual(alt, 1.0)
    self.assertEqual(speed, 2.23694)
    self.assertEqual(geohash, 'c21efweg66fd')
    self.assertEqual(elapsed_duration_ms, 10)
    self.assertEqual(elapsed_distance_m, 33)
    self.assertEqual(tps_voltage, 2.0)
    self.assertEqual(water_temp_voltage, 3.0)
    self.assertEqual(oil_pressure_voltage, 4.0)
    self.assertEqual(rpm, 1000)
    self.assertEqual(afr, 14.7)
    self.assertEqual(fuel_level_voltage, 5.0)
    self.assertEqual(accelerometer_x, 0.0)
    self.assertEqual(accelerometer_y, 1.7)
    self.assertEqual(accelerometer_z, 1.2)
    self.assertEqual(pitch, 0.2)
    self.assertEqual(roll, 5.0)
    self.assertEqual(gyro_x, 0.0)
    self.assertEqual(gyro_y, 1.0)
    self.assertEqual(gyro_z, 2.5)
    self.assertEqual(front_brake_pressure_voltage, 3.5)
    self.assertEqual(rear_brake_pressure_voltage, 2.5)
    self.assertEqual(battery_voltage, 13.5)
    self.assertEqual(oil_temp_voltage, 2.5)
    self.assertEqual(labjack_temp_f, 77.9)
    self.assertEqual(lf_tire_temp_inner, 170,0)
    self.assertEqual(lf_tire_temp_middle, 180.0)
    self.assertEqual(lf_tire_temp_outer, 200.0)
    self.assertEqual(rf_tire_temp_inner, 190.0)
    self.assertEqual(rf_tire_temp_middle, 190.0)
    self.assertEqual(rf_tire_temp_outer, 190.0)
    self.assertEqual(lr_tire_temp_inner, 0.0)
    self.assertEqual(lr_tire_temp_middle, 0.0)
    self.assertEqual(lr_tire_temp_outer, 0.0)
    self.assertEqual(rr_tire_temp_inner, 0.0)
    self.assertEqual(rr_tire_temp_middle, 0.0)
    self.assertEqual(rr_tire_temp_outer, 0.0)

  def testExportPointArrivesBeforeLap(self):
    point = gps_pb2.Point()
    self.pusher.ExportPoint(point, 99, self.cursor)
    self.assertEqual(1, len(self.pusher.retry_point_queue))

  def testGetPointFromQueue(self):
    with self.subTest(name='Success'):
      point = gps_pb2.Point()
      self.pusher.AddPointToQueue(point, 1)
      result = self.pusher.GetPointFromQueue()
      self.assertTrue(result)
      if result:
        returned_point, returned_lap_number = result
        self.assertEqual(point, returned_point)
        self.assertEqual(1, returned_lap_number)
    with self.subTest(name='Retry Queue'):
      point = gps_pb2.Point()
      self.pusher.retry_point_queue.append((point, 2))
      result = self.pusher.GetPointFromQueue()
      self.assertTrue(result)
      if result:
        returned_point, returned_lap_number = result
        self.assertEqual(point, returned_point)
        self.assertEqual(2, returned_lap_number)
    with self.subTest(name='Retry and Point Queue'):
      point = gps_pb2.Point()
      self.pusher.AddPointToQueue(point, 1)
      point = gps_pb2.Point()
      self.pusher.retry_point_queue.append((point, 2))
      result = self.pusher.GetPointFromQueue()
      self.assertTrue(result)
      if result:
        returned_point, returned_lap_number = result
        self.assertEqual(point, returned_point)
        self.assertEqual(1, returned_lap_number)

  @mock.patch.object(timescale, 'ConnectToDB')
  def testDo(self, mock_conn):
    mock_conn.return_value = self.conn
    lap = gps_pb2.Lap()
    lap.duration.FromMilliseconds(90 * 1000)
    lap.number = 1
    point = lap.points.add()
    point.alt = 1
    point.speed = 1
    point.lat = 45.69545832462609
    point.lon = -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    point.accelerometer_x = 0.0
    point.accelerometer_y = 1.7
    point.accelerometer_z = 1.2
    self.pusher.lap_queue.put(lap.SerializeToString())
    self.pusher.AddPointToQueue(point, 1)
    with self.subTest(name='Success'):
      self.pusher.Do()
      self.cursor.execute('SELECT count(*) FROM sessions')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM laps')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM points')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(0, len(self.pusher.point_queue))
    with self.subTest(name='Second Point'):
      self.pusher.AddPointToQueue(point, 1)
      self.pusher.Do()
      self.cursor.execute('SELECT count(*) FROM sessions')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM laps')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM points')
      self.assertEqual(2, self.cursor.fetchone()[0])
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(0, len(self.pusher.point_queue))
    with self.subTest(name='Lap Duration'):
      self.pusher.lap_duration_queue.put((1, lap.duration))
      self.pusher.AddPointToQueue(point, 1)
      self.pusher.Do()
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(0, len(self.pusher.point_queue))
    with self.subTest(name='Point Too Early'):
      self.pusher.point_queue.append((point.SerializeToString(), 2))
      self.pusher.Do()
      self.cursor.execute('SELECT count(*) FROM sessions')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM laps')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM points')
      self.assertEqual(3, self.cursor.fetchone()[0])
      self.assertEqual(1, len(self.pusher.retry_point_queue))
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(1, len(self.pusher.retry_point_queue))
    with self.subTest(name='Exception'):
      lap.number = 2
      lap.duration.FromMilliseconds(90 * 1000)
      self.pusher.lap_queue.put(lap.SerializeToString())
      self.pusher.lap_duration_queue.put((1, lap.duration))
      self.pusher.AddPointToQueue(point, 1)
      with mock.patch.object(self.pusher, 'ExportPoint') as mock_export:
        mock_export.side_effect = psycopg2.Error
        self.pusher.Do()
        self.assertEqual(1, self.pusher.lap_queue.qsize())
        self.assertEqual(1, self.pusher.lap_duration_queue.qsize())
        self.assertEqual(1, len(self.pusher.retry_point_queue))

  def testDoCommitCycle(self):
    """Ensures points aren't dropped if errrors arrive between commits."""
    point = gps_pb2.Point()
    point.alt = 1
    point.speed = 1
    point.lat = 45.69545832462609
    point.lon = -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    point.accelerometer_x = 0.0
    point.accelerometer_y = 1.7
    point.accelerometer_z = 1.2
    self.assertEqual(0, len(self.pusher.point_queue))
    self.pusher.AddPointToQueue(point, 1)
    self.pusher.Do()
    self.pusher.AddPointToQueue(point, 1)
    self.pusher.Do()
    with mock.patch.object(self.pusher, '_Commit') as mock_commit:
      mock_commit.side_effect = psycopg2.Error
      self.pusher.AddPointToQueue(point, 1)
      self.pusher.Do()
    self.assertEqual(3, len(self.pusher.retry_point_queue))


if __name__ == '__main__':
  absltest.main()
