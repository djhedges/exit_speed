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
"""Converts a data log generated by exit speed to the new proto format."""
import os

from absl import app
from absl import flags
from absl import logging

from exit_speed import data_logger
from exit_speed import exit_speed_pb2
from exit_speed import tracks

FLAGS = flags.FLAGS
flags.DEFINE_string('old_data_path', None, 'Path to an old data file.')


SENSOR_PROTO = {
  'GpsSensor': exit_speed_pb2.Gps,
  'AccelerometerSensor': exit_speed_pb2.Accelerometer,
  'GyroscopeSensor': exit_speed_pb2.Gyroscope,
  'LabjackSensor': exit_speed_pb2.Labjack,
  'WBO2Sensor': exit_speed_pb2.WBO2,
}


def NewPrefix(old_data_path, track, sensor_name, session_time):
  base_dir = os.path.join(*old_data_path.split(os.path.sep)[:-1])
  new_prefix = os.path.join(
      os.path.join('/', base_dir),
      track.name,
      session_time,
      sensor_name)
  logging.info('New prefix: %s', new_prefix)
  return new_prefix


def main(unused_argv):
  flags.mark_flag_as_required('old_data_path')
  old_logger = data_logger.Logger(FLAGS.old_data_path)
  old_protos = list(old_logger.ReadProtos())
  session_time = old_protos[0].time.ToJsonString()
  track = tracks.FindClosestTrack({'lat': old_protos[0].lat,
                                   'lon': old_protos[0].lon})
  new_loggers = {}
  for sensor_name, proto_class in SENSOR_PROTO.items():
    new_loggers[sensor_name] = data_logger.Logger(
        NewPrefix(FLAGS.old_data_path, track, sensor_name, session_time),
        proto_class=proto_class)
  count = 0
  for old_point in old_protos:
    logging.log_every_n_seconds(logging.INFO, old_point, 30)
    count += 1
    gps_proto = exit_speed_pb2.Gps(time=old_point.time,
                                   lat=old_point.lat,
                                   lon=old_point.lon,
                                   alt=old_point.alt,
                                   speed_ms=old_point.speed_ms)
    gps_logger = new_loggers['GpsSensor']
    gps_logger.WriteProto(gps_proto)
    logging.log_every_n_seconds(logging.INFO, gps_proto, 30)
    if old_point.accelerometer_x:
      accel_proto = exit_speed_pb2.Accelerometer(
          time=old_point.time,
          accelerometer_x=old_point.accelerometer_x,
          accelerometer_y=old_point.accelerometer_y,
          accelerometer_z=old_point.accelerometer_z)
      accel_logger = new_loggers['AccelerometerSensor']
      accel_logger.WriteProto(accel_proto)
      logging.log_every_n_seconds(logging.INFO, accel_proto, 30)
    if old_point.gyro_x:
      gyro_proto = exit_speed_pb2.Gyroscope(
          time=old_point.time,
          gyro_x=old_point.gyro_x,
          gyro_y=old_point.gyro_y,
          gyro_z=old_point.gyro_z)
      gyro_logger = new_loggers['GyroscopeSensor']
      gyro_logger.WriteProto(gyro_proto)
      logging.log_every_n_seconds(logging.INFO, gyro_proto, 30)
    if old_point.water_temp_voltage:
      labjack_proto = exit_speed_pb2.Labjack(
          time=old_point.time,
          labjack_temp_f=old_point.labjack_temp_f,
          battery_voltage=old_point.battery_voltage,
          front_brake_pressure_voltage=old_point.front_brake_pressure_voltage,
          fuel_level_voltage=old_point.fuel_level_voltage,
          fuel_pressure_voltage=old_point.fuel_pressure_voltage,
          oil_pressure_voltage=old_point.oil_pressure_voltage,
          oil_temp_voltage=old_point.oil_temp_voltage,
          rear_brake_pressure_voltage=old_point.rear_brake_pressure_voltage,
          water_temp_voltage=old_point.water_temp_voltage)
      labjack_logger = new_loggers['LabjackSensor']
      labjack_logger.WriteProto(labjack_proto)
      logging.log_every_n_seconds(logging.INFO, labjack_proto, 30)
    if old_point.rpm or old_point.tps_voltage:
      wbo2_proto = exit_speed_pb2.WBO2(
          time=old_point.time,
          afr=old_point.afr,
          rpm=old_point.rpm,
          tps_voltage=old_point.tps_voltage)
      wbo2_logger = new_loggers['WBO2Sensor']
      wbo2_logger.WriteProto(wbo2_proto)
      logging.log_every_n_seconds(logging.INFO, wbo2_proto, 30)
    logging.log_every_n_seconds(logging.INFO, 'Written %d protos', 10, count)
  logging.info('Final proto count %d', count)


if __name__ == '__main__':
  app.run(main)
