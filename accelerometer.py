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
"""ADXL345 accelerometer."""

from typing import Text
from typing import Tuple
import time
from absl import app
import board
import busio
import adafruit_adxl34x


class Accelerometer(object):
  """Measures the G forces the car experiences."""
  GRAVITY = 9.81
  X_LOW = -10.4735022
  Y_LOW = -10.1596894
  Z_LOW = -8.9828914
  X_HIGH = 9.7674234
  Y_HIGH = 10.0812362
  Z_HIGH = 10.8657682

  def __init__(self):
    self.i2c = busio.I2C(board.SCL, board.SDA)
    self.accelerometer = adafruit_adxl34x.ADXL345(self.i2c)
    self.accelerometer.range = adafruit_adxl34x.Range.RANGE_16_G

  def CorrectValue(self, axis: Text, value: float) -> float:
    """Returns the values after correcting for calibration.

    Args:
      axis: A string of the axis such as x,y,z.
      value: A value from self.accelerometer.acceleration

    https://learn.sparkfun.com/tutorials/adxl345-hookup-guide#calibration
    """
    low = getattr(self, '%s_LOW' % axis.upper())
    high = getattr(self, '%s_HIGH' % axis.upper())
    offset = 0.5 * (high + low)
    gain = 0.5 * ((high - low) / 9.81)
    return (value - offset) / gain

  def GetGForces(self) -> Tuple[float, float, float]:
    """Returns the number of G forces measured in each dirrection."""
    x, y, z = self.accelerometer.acceleration
    print(x, y, z)
    x = self.CorrectValue('x', x)
    y = self.CorrectValue('y', y)
    z = self.CorrectValue('z', z)
    return x / self.GRAVITY, y / self.GRAVITY, z / self.GRAVITY


def main(unused_argv):
  accel = Accelerometer()
  while True:
    print('%.2f %.2f %.2f' % accel.GetGForces())
    time.sleep(1)


if __name__ == '__main__':
  app.run(main)
