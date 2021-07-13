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
"""MLX90640 InfraRed sensor.

https://github.com/melexis-fir/mlx9064x-driver-py
"""

import statistics
from typing import List
from absl import app
from mlx import mlx90640


class InfraRedSensor(object):
  """Measures a 32x24 grid of temperature."""

  def __init__(self, com_port='I2C-1', i2c_addr=0x33, frame_rate=1.0,
      emissivity=0.9):
    self.frame_rate = frame_rate
    self.mlx = mlx90640.Mlx9064x(
        com_port, i2c_addr=i2c_addr, frame_rate=frame_rate)
    self.mlx.init()
    self.mlx.emissivity = emissivity

  def ReadFrame(self) -> List[float]:
    """Reads a frame from the infrared sensor."""
    try:
      frame = self.mlx.read_frame()
    except mlx90640.I2CAcknowledgeError:
      self.mlx.clear_error(self.frame_rate)
    frame = self.mlx.do_compensation(frame)
    frame = self.mlx.do_handle_bad_pixels(frame)
    return frame

  def FormatFrame(self, frame: List[float]) -> List[List[float]]:
    """Formats a frame by pixel positions of rows and columns."""
    formatted = []
    for row_number in range(24):
      formatted.append(frame[row_number:row_number + 32])
    return formatted


class TireSensor(InfraRedSensor):

  def GetTempsByColumn(self):
    formated_frame = sensor.FormatFrame(sensor.ReadFrame())
    column_temps = {}
    col_index = 0
    for row in formated_frame:
      for temp in row:
        column_temps.setdefault(col_index, []).append(temp)
      col_index += 1
    return column_temps

  def GetMedianColumnTemps(self):
    column_temps = self.GetTempsByColumn()
    median_temps = {}
    for column, temps in column_temps.items():
      median_temps[column] = statistics.median(temps)
    return median_temps


def main(unused_argv):
  sensor = TireSensor()
  print(sensor.GetMedianColumnTemps())


if __name__ == '__main__':
  app.run(main)
