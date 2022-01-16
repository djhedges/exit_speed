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
"""FXOS8700 accelerometer."""
import math
import time
from typing import Text
from typing import Tuple

import adafruit_fxos8700
import board
import busio
from absl import app

from exit_speed import gps_pb2
from exit_speed import sensor


class Accelerometer(object):
  """Measures the G forces the car experiences."""
  GRAVITY = 9.81
  X_LOW = -9.7459664498
  Y_LOW = -9.8632147572
  Z_LOW = -9.4660062056
  X_HIGH = 10.420742422999998
  Y_HIGH = 9.164510558
  Z_HIGH = 10.301101292999999

  def __init__(self):
    self.i2c = busio.I2C(board.SCL, board.SDA)
    self.accelerometer = adafruit_fxos8700.FXOS8700(
        self.i2c, accel_range=adafruit_fxos8700.ACCEL_RANGE_8G)

  def CorrectValue(self, axis: Text, value: float) -> float:
    """Returns the values after correcting for calibration.

    Args:
      axis: A string of the axis such as x,y,z.
      value: A value from self.accelerometer.accelerometer

    https://learn.sparkfun.com/tutorials/adxl345-hookup-guide#calibration
    https://www.nxp.com/docs/en/application-note/AN4399.pdf
    """
    low = getattr(self, '%s_LOW' % axis.upper())
    high = getattr(self, '%s_HIGH' % axis.upper())
    offset = 0.5 * (high + low)
    gain = 0.5 * ((high - low) / 9.81)
    return (value - offset) / gain

  def GetGForces(self) -> Tuple[float, float, float]:
    """Returns the number of G forces measured in each direction."""
    x, y, z = self.accelerometer.accelerometer
    x = self.CorrectValue('x', x)
    y = self.CorrectValue('y', y)
    z = self.CorrectValue('z', z)
    return x / self.GRAVITY, y / self.GRAVITY, z / self.GRAVITY

  def CalcPitchAndRoll(self, x_gs, y_gs, z_gs) -> Tuple[float, float]:
    """Calculates the pitch and roll based on the G readings."""
    pitch = ((math.atan2(x_gs, math.sqrt(y_gs * y_gs + z_gs * z_gs)) * 180) /
        math.pi)
    roll = (math.atan2(-y_gs, z_gs) * 180)  / math.pi
    return pitch, roll


class AccelerometerProcess(sensor.SensorBase):
  """Populates the SensorBase.point_queue with accelerometer values per loop."""

  def Loop(self):
    """Adds point data with accelerometer values to point queue."""
    accel = Accelerometer()
    frequency_hz = int(
        self.config.get('accelerometer', {}).get('frequency_hz')) or 10
    while not self.stop_process_signal.value:
      cycle_time = time.time()
      x, y, z = accel.GetGForces()
      point = gps_pb2.Point()
      point.accelerometer_x = x
      point.accelerometer_y = y
      point.accelerometer_z = z
      pitch, roll = accel.CalcPitchAndRoll(x, y, z)
      point.pitch = pitch
      point.roll = roll
      self.AddPointToQueue(point)
      time.sleep(sensor.SleepBasedOnHertz(cycle_time, frequency_hz))



def main(unused_argv):
  accel = Accelerometer()
  while True:
    x, y, z = accel.GetGForces()
    print('%.2f %.2f %.2f' % (x, y, z))
    print('Roll: %.2f, Pitch: %.2f' % accel.CalcPitchAndRoll(x, y, z))
    time.sleep(1)


if __name__ == '__main__':
  app.run(main)
