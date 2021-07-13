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
import numpy
from typing import Dict
from typing import List
from typing import Tuple
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


def FindTireIndex(jumps) -> int:
  first_jump = False
  index = 0
  for jump in jumps:
    if jump:
      first_jump = True
    if not jump and first_jump:
      return index
    index += 1
  return 0


class TireSensor(InfraRedSensor):
  # Temperature delta from tire edge to air/suspension.
  TEMP_EDGE_SENSITIVITY = 40

  def GetTempsByColumn(self) -> Dict[int, List[float]]:
    """Returns temperature in Celsius per column where key is column index."""
    formated_frame = self.FormatFrame(self.ReadFrame())
    column_temps = {}
    col_index = 0
    for row in formated_frame:
      for temp in row:
        column_temps.setdefault(col_index, []).append(temp)
      col_index += 1
    return column_temps

  def GetMedianColumnTemps(self) -> Dict[int, float]:
    """Returns the median temperature in Celsius per column."""
    column_temps = self.GetTempsByColumn()
    median_temps = {}
    for column, temps in column_temps.items():
      median_temps[column] = statistics.median(temps)
    return median_temps

  def GetTireTemps(self) -> Tuple[float, float, float]:
    """Attempts to find the edge of the tire based on temperature changes."""
    median_temps = self.GetMedianColumnTemps()
    diff = numpy.diff(list(median_temps.values()))
    jumps = abs(diff) > self.TEMP_EDGE_SENSITIVITY
    reverse_jumps = list(jumps)
    reverse_jumps.reverse()
    left_tire_index = FindTireIndex(jumps)
    right_tire_index = len(median_temps) - FindTireIndex(reverse_jumps) - 1
    middle_tire_index = round(statistics.mean(
        [left_tire_index, right_tire_index]))
    return (
        median_temps[left_tire_index],
        median_temps[middle_tire_index],
        median_temps[right_tire_index])


def main(unused_argv):
  sensor = TireSensor()
  while True:
    print(sensor.GetMedianColumnTemps())
    print(sensor.GetTireTemps())


if __name__ == '__main__':
  app.run(main)
