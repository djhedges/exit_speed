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
"""FXAS21002C gyroscope."""
import math
import time
from typing import Tuple

import adafruit_fxas21002c
import board
import busio
from absl import app

from exit_speed import gps_pb2
from exit_speed import sensor


class Gyroscope(object):
  """Measures rotational rate."""

  def __init__(self):
    self.i2c = busio.I2C(board.SCL, board.SDA)
    self.sensor = adafruit_fxas21002c.FXAS21002C(self.i2c)

  def GetRotationalValues(self) -> Tuple[float, float, float]:
    """Returns Gyroscope values in degrees."""
    gyro_x, gyro_y, gyro_z = self.sensor.gyroscope
    return (math.degrees(gyro_x),
            math.degrees(gyro_y),
            math.degrees(gyro_z))


class GyroscopeProcess(sensor.SensorBase):
  """Populates the SensorBase.point_queue with gyroscope values per loop."""

  def Loop(self):
    """Adds point data with gryoscope values to point queue."""
    gyro = Gyroscope()
    frequency_hz = int(
        self.config.get('gyroscope', {}).get('frequency_hz')) or 10
    while not self.stop_process_signal.value:
      cycle_time = time.time()
      x, y, z = gyro.GetRotationalValues()
      point = gps_pb2.Point()
      point.gyro_x = x
      point.gyro_y = y
      point.gyro_z = z
      self.AddPointToQueue(point)
      time.sleep(sensor.SleepBasedOnHertz(cycle_time, frequency_hz))



def main(unused_argv):
  gyro = Gyroscope()
  while True:
    x, y, z = gyro.GetRotationalValues()
    print('%.2f %.2f %.2f' % (x, y, z))
    time.sleep(1)


if __name__ == '__main__':
  app.run(main)
