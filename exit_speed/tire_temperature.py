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
import multiprocessing
import socket
import statistics
import struct
from typing import Dict
from typing import List
from typing import Text
from typing import Tuple

import numpy
from absl import app
from absl import flags
from absl import logging
from mlx import mlx90640

from exit_speed import gps_pb2
from exit_speed import sensor

FLAGS = flags.FLAGS
flags.DEFINE_string('ip_addr', None,
                    'IP address of the main Exit Speed process.')
flags.DEFINE_integer('port', None,
                     'Port number that corresponds to this corner.')


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
    logging.log_every_n_seconds(
        logging.INFO, 'Raw frame: \n%s', 60 * 5, frame)
    return frame

  def FormatFrame(self, frame: List[float]) -> List[List[float]]:
    """Formats a frame by pixel positions of rows and columns."""
    formatted = []
    for row_number in range(24):
      formatted.append(frame[row_number:row_number + 32])
    logging.log_every_n_seconds(
        logging.INFO, 'Formatted frame: \n%s', 60 * 5, formatted)
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
  """Tire temperature sensor."""
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
    logging.log_every_n_seconds(
        logging.INFO, 'Column temps: \n%s', 60 * 5, column_temps)
    return column_temps

  def GetMedianColumnTemps(self) -> Dict[int, float]:
    """Returns the median temperature in Celsius per column."""
    column_temps = self.GetTempsByColumn()
    median_temps = {}
    for column, temps in column_temps.items():
      median_temps[column] = statistics.median(temps)
    logging.log_every_n_seconds(
        logging.INFO, 'Median temps: \n%s', 60 * 5, median_temps)
    return median_temps

  def GetTireTemps(self) -> Tuple[float, float, float]:
    """Attempts to find the edge of the tire based on temperature changes."""
    median_temps = self.GetMedianColumnTemps()
    diff = numpy.diff(list(median_temps.values()))
    jumps = abs(diff) > self.TEMP_EDGE_SENSITIVITY
    reverse_jumps = list(jumps)
    reverse_jumps.reverse()
    inner_tire_index = FindTireIndex(jumps)
    outer_tire_index = len(median_temps) - FindTireIndex(reverse_jumps) - 1
    middle_tire_index = round(statistics.mean(
        [inner_tire_index, outer_tire_index]))
    logging.log_every_n_seconds(
        logging.INFO, 'Inner index: %s, Middle index: %s, Outer index:%s',
        60 * 5, inner_tire_index, middle_tire_index, outer_tire_index,)
    return (
        median_temps[inner_tire_index],
        median_temps[middle_tire_index],
        median_temps[outer_tire_index])


class TireSensorClient(object):
  """Client for sending data from the Pi zeros."""

  def __init__(self, ip_addr: Text, port: int):
    self.ip_addr = ip_addr
    self.port = port
    self.sensor = TireSensor()
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  def ReadAndSendData(self):
    temps = struct.pack('fff', *self.sensor.GetTireTemps())
    self.sock.sendto(temps, (self.ip_addr, self.port))

  def Loop(self):
    logging.info('Sending tire temperature data...')
    while True:
      self.ReadAndSendData()


class TireSensorServer(sensor.SensorBase):
  """Server for receiving data from the Pi zeros."""

  def __init__(
      self,
      corner: Text,
      ip_addr: Text,
      port: int,
      config: Dict,
      point_queue: multiprocessing.Queue,
      start_process: bool=True):
    self.corner = corner
    self.ip_addr = ip_addr
    self.port = port
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    super().__init__(config, point_queue, start_process=start_process)

  def Loop(self):
    self.sock.bind((self.ip_addr, self.port))
    while not self.stop_process_signal.value:
      data, _ = self.sock.recvfrom(1024)
      inside, middle, outside = struct.unpack('fff', data)
      point = gps_pb2.Point()
      corner = getattr(point, self.corner)
      setattr(corner, 'inner', (inside * 9/5) + 32)
      setattr(corner, 'middle', (middle * 9/5) + 32)
      setattr(corner, 'outer', (outside * 9/5) + 32)
      self.AddPointToQueue(point)


class MultiTireInterface(object):
  """Main class used by exit speed to hold each tire server."""

  def __init__(self, config: Dict, point_queue: multiprocessing.Queue):
    """Initializer.

    Args:
      config: A dict created from parsing the exit speed yaml config.
    """
    self.servers = {}
    for corner, ip_port in config['tire_temps'].items():
      self.servers[corner] = TireSensorServer(corner,
                                              ip_port['ip_addr'],
                                              int(ip_port['port']),
                                              config,
                                              point_queue)



def main(unused_argv):
  client = TireSensorClient(FLAGS.ip_addr, FLAGS.port)
  client.Loop()


if __name__ == '__main__':
  app.run(main)
