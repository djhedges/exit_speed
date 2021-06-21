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
"""Used to cleanup database entries created during testing."""

from absl import app
from absl import flags
from absl import logging
import timescale
import os
import glob
import data_logger
import gps_pb2
import exit_speed

def GetIdAndTime(conn):
  with conn.cursor() as cursor:
    cursor.execute("""
    SELECT id, time FROM sessions
    WHERE id > 497
    """)
    return cursor.fetchall()

def GetPoints(conn, session_id):
  with conn.cursor() as cursor:
    cursor.execute("""
    SELECT * FROM points
    WHERE session_id = %s
    ORDER BY time
    """, (session_id,))
    return cursor.fetchall()

def main(unused_argv):
  es = exit_speed.ExitSpeed()
  with timescale.ConnectToDB() as conn:
    id_time = GetIdAndTime(conn)
    for session_id, time in id_time:
      db_points = GetPoints(conn, session_id)
      new_points = []
      for db_point in db_points:
        new_point = gps_pb2.Point()
        new_point.time.FromDatetime(db_point[0])
        new_point.lat = db_point[3]
        new_point.lon = db_point[4]
        new_point.alt = db_point[5]
        new_point.speed = db_point[6]
        new_point.geohash = db_point[7]
        new_point.elapsed_duration_ms = db_point[8]
        new_point.elapsed_distance_m = db_point[9]
        new_point.tps_voltage = db_point[10]
        new_point.water_temp_voltage = db_point[11]
        new_point.oil_pressure_voltage = db_point[12]
        new_point.rpm = db_point[13]
        new_point.afr = db_point[14]
        new_point.fuel_level_voltage = db_point[15]
        new_point.accelerometer_x = db_point[16]
        new_point.accelerometer_y = db_point[17]
        new_point.accelerometer_z = db_point[18]
        new_point.pitch = db_point[19]
        new_point.roll = db_point[20]
        new_point.gyro_x = db_point[21]
        new_point.gyro_y = db_point[22]
        new_point.gyro_z = db_point[23]
        new_point.front_brake_pressure_voltage = db_point[24]
        new_point.rear_brake_pressure_voltage = db_point[25]
        new_point.battery_voltage = db_point[26]
        new_point.oil_temp_voltage = db_point[27]
        new_points.append(new_point)
      log_file_prefix = es.GetLogFilePrefix(new_points[0])
      logger = data_logger.Logger(log_file_prefix)
      print(log_file_prefix)
      for new_point in new_points:
        logger.WriteProto(new_point)


if __name__ == '__main__':
  app.run(main)
