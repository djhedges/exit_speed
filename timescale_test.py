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

import time
import unittest
from absl.testing import absltest
import config_lib
import gps_pb2
import psycopg2
import timescale
import testing.postgresql
import mock

Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


def tearDownModule():
  Postgresql.clear_cache()


class TestTimescale(unittest.TestCase):

  def setUp(self):
    self.postgresql = Postgresql()
    with open('testdata/timescale_schema') as schema_file:
      statements = ''.join(schema_file.readlines())
    conn = psycopg2.connect(**self.postgresql.dsn())
    cursor = conn.cursor()
    cursor.execute(statements)
    conn.commit()
    self.conn = timescale._GetConnWithPointPrepare(conn)
    self.cursor = self.conn.cursor()
    point = gps_pb2.Point()
    point.time.FromJsonString('2020-09-13T01:36:38.600Z')
    self.pusher = timescale.Pusher(start_process=False)
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

  def testGetElapsedTime(self):
    point = gps_pb2.Point()
    point.time.FromSeconds(10)
    self.assertEqual(0, self.pusher.GetElapsedTime(point, 1))
    point = gps_pb2.Point()
    point.time.FromSeconds(20)
    self.assertEqual(10 * 1000, self.pusher.GetElapsedTime(point, 1))

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
    point.lon -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    self.pusher.ExportPoint(point, 1, self.cursor)
    self.cursor.execute('SELECT * FROM points')
    (time, session_id, lap_id, alt, speed, geohash, elapsed_duration_ms,
     tps_voltage, water_temp_voltage, oil_pressure_voltage, rpm, afr,
     fuel_level_voltage) = self.cursor.fetchone()
    self.assertEqual(alt, 1.0)
    self.assertEqual(speed, 2.23694)
    self.assertEqual(geohash, 'u005bn8524b4')
    self.assertEqual(elapsed_duration_ms, 0.0)
    self.assertEqual(tps_voltage, 2.0)
    self.assertEqual(water_temp_voltage, 3.0)
    self.assertEqual(oil_pressure_voltage, 4.0)
    self.assertEqual(rpm, 1000)
    self.assertEqual(afr, 14.7)
    self.assertEqual(fuel_level_voltage, 5.0)

  def testExportPointArrivesBeforeLap(self):
    point = gps_pb2.Point()
    self.pusher.ExportPoint(point, 99, self.cursor)
    self.assertEqual(1, len(self.pusher.point_queue))

  def testGetPointFromQueue(self):
    point = gps_pb2.Point()
    self.pusher.point_queue.append((point, 1))
    returned_point, returned_lap_number = self.pusher.GetPointFromQueue()
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
    point.lon -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    self.pusher.lap_queue.put(lap)
    self.pusher.point_queue.append((point, 1))
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
      self.pusher.point_queue.append((point, 1))
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
      self.pusher.point_queue.append((point, 1))
      self.pusher.Do()
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(0, len(self.pusher.point_queue))
    with self.subTest(name='Point Too Early'):
      self.pusher.point_queue.append((point, 2))
      self.pusher.Do()
      self.cursor.execute('SELECT count(*) FROM sessions')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM laps')
      self.assertEqual(1, self.cursor.fetchone()[0])
      self.cursor.execute('SELECT count(*) FROM points')
      self.assertEqual(3, self.cursor.fetchone()[0])
      self.assertEqual(1, len(self.pusher.point_queue))
      self.assertEqual(0, self.pusher.lap_queue.qsize())
      self.assertEqual(0, self.pusher.lap_duration_queue.qsize())
      self.assertEqual(1, len(self.pusher.point_queue))
    with self.subTest(name='Exception'):
      lap.number = 2
      lap.duration.FromMilliseconds(90 * 1000)
      self.pusher.lap_queue.put(lap)
      self.pusher.lap_duration_queue.put((1, lap.duration))
      self.pusher.point_queue.append((point, 1))
      with mock.patch.object(self.pusher, 'ExportPoint') as mock_export:
        mock_export.side_effect = psycopg2.Error
        self.pusher.Do()
        self.assertEqual(1, self.pusher.lap_queue.qsize())
        self.assertEqual(1, self.pusher.lap_duration_queue.qsize())
        self.assertEqual(1, len(self.pusher.point_queue))

  def testDoCommitCycle(self):
    """Ensures points aren't dropped if errrors arrive between commits."""
    point = gps_pb2.Point()
    point.alt = 1
    point.speed = 1
    point.lat = 45.69545832462609
    point.lon -121.52551179751754
    point.tps_voltage = 2
    point.water_temp_voltage = 3
    point.oil_pressure_voltage = 4
    point.rpm = 1000
    point.afr = 14.7
    point.fuel_level_voltage = 5
    self.assertEqual(0, len(self.pusher.point_queue))
    self.pusher.point_queue.append((point, 1))
    self.pusher.Do()
    self.pusher.point_queue.append((point, 1))
    self.pusher.Do()
    with mock.patch.object(self.pusher, '_Commit') as mock_commit:
      mock_commit.side_effect = psycopg2.Error
      self.pusher.point_queue.append((point, 1))
      self.pusher.Do()
    self.assertEqual(3, len(self.pusher.point_queue))


if __name__ == '__main__':
  absltest.main()