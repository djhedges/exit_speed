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
"""Client library for the reflector.
"""

from absl import app
import grpc
import reflector_pb2
import reflector_pb2_grpc


def main(unused_argv):
  channel = grpc.insecure_channel('unix:///tmp/exit_speed.sock')
  stub = reflector_pb2_grpc.ReflectStub(channel)
  point_update = reflector_pb2.PointUpdate()
  point_update.point.time.FromJsonString('2020-09-13T01:36:38.600Z')
  point_update.point.alt = 1
  point_update.point.speed = 1
  point_update.point.lat = 45.69545832462609
  point_update.point.lon = -121.52551179751754
  point_update.point.tps_voltage = 2
  point_update.point.water_temp_voltage = 3
  point_update.point.oil_pressure_voltage = 4
  point_update.point.rpm = 1000
  point_update.point.afr = 14.7
  point_update.point.fuel_level_voltage = 5
  point_update.point.accelerometer_x = 0.0
  point_update.point.accelerometer_y = 1.7
  point_update.point.accelerometer_z = 1.2
  point_update.point.pitch = 0.2
  point_update.point.roll = 5.0
  point_update.point.gyro_x = 0.0
  point_update.point.gyro_y = 1.0
  point_update.point.gyro_z = 2.5
  point_update.point.geohash = 'c21efweg66fd'
  response = stub.ExportPoint(point_update)
  print(response)


if __name__ == '__main__':
  app.run(main)
