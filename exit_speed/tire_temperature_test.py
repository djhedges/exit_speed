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
"""Unitests for tire_temperature.py"""
import multiprocessing
import time
import unittest

import mock
from absl.testing import absltest
from mlx import mlx90640

from exit_speed import gps_pb2
from exit_speed import tire_temperature

def _CreateRawFrame():
  frame = []
  for _ in range(32 * 24):
    frame.append(30.0)
  return frame

def _CreateFormattedFrame():
  formatted_frame = []
  for _ in range(32):
    row = []
    temp = 0
    for _ in range(24):
      row.append(temp)
      temp += 10
    formatted_frame.append(row)
  return formatted_frame


class MockMlx9064xSensorBase(unittest.TestCase):

  def setUp(self):
    super().setUp()
    patch = mock.patch.object(mlx90640, 'Mlx9064x')
    self.addCleanup(patch.stop)
    self.mock_mlx = patch.start()


class TestInfraRedSensor(MockMlx9064xSensorBase):
  """Infrared Sensor unittests."""

  def setUp(self):
    super().setUp()
    self.sensor = tire_temperature.InfraRedSensor()

  def testReadFrame(self):
    self.mock_mlx.read_frame.return_value = _CreateRawFrame()
    self.sensor.ReadFrame()

  def testFormatFrame(self):
    raw_frame = _CreateRawFrame()
    formatted_frame = self.sensor.FormatFrame(raw_frame)
    row_count = 0
    for row in formatted_frame:
      row_count += 1
      self.assertEqual(32, len(row))
    self.assertEqual(24, row_count)


class TestTireSensor(MockMlx9064xSensorBase):
  """Tire Temperature unittests."""

  def setUp(self):
    super().setUp()
    self.sensor = tire_temperature.TireSensor()

  def testGetTempsByColumn(self):
    expected = {}
    col_index = 0
    for _ in range(32):
      temp = 0
      temps = []
      for _ in range(24):
        temps.append(temp)
        temp += 10
      expected[col_index] = temps
      col_index += 1
    with mock.patch.object(self.sensor, 'FormatFrame') as mock_format_frame:
      mock_format_frame.return_value = _CreateFormattedFrame()
      self.assertDictEqual(expected, self.sensor.GetTempsByColumn())

  def testGetMedianColumnTemps(self):
    expected = {}
    col_index = 0
    for _ in range(32):
      expected[col_index] = 115.0
      col_index += 1
    with mock.patch.object(self.sensor, 'FormatFrame') as mock_format_frame:
      mock_format_frame.return_value = _CreateFormattedFrame()
      self.assertDictEqual(expected, self.sensor.GetMedianColumnTemps())

  def testGetTireTemps(self):
    column_temp = {
        # Air
        0: 80.0,
        1: 80.0,
        2: 80.0,
        3: 80.0,
        4: 80.0,
        5: 80.0,
        6: 80.0,
        7: 80.0,
        8: 80.0,
        9: 135.0,  # Avg temp between tire and ambient air
        # Inside tire
        10: 190.0,
        11: 190.0,
        12: 190.0,
        13: 190.0,
        14: 190.0,
        # Middle Tire
        15: 200.0,
        16: 200.0,
        17: 200.0,
        18: 200.0,
        19: 200.0,
        20: 200.0,
        # Outside Tire
        21: 230.0,
        22: 230.0,
        23: 230.0,
        24: 230.0,
        # Shock heat/spindle
        25: 185.0,  # Avg temp between tire & spindle
        26: 140.0,
        27: 140.0,
        28: 140.0,
        29: 140.0,
        30: 140.0,
        31: 140.0,
    }
    expected = (190.0, 200.0, 230.0)
    with mock.patch.object(self.sensor, 'GetMedianColumnTemps') as mock_col:
      mock_col.return_value = column_temp
      self.assertTupleEqual(expected, self.sensor.GetTireTemps())


class TestClientServer(unittest.TestCase):
  """Tests the ability for the Pi zero client to send data to the server."""

  def testClientServer(self):
    mock_sensor = mock.create_autospec(tire_temperature.TireSensor)
    mock_sensor.GetTireTemps.return_value = (87.0, 93.0, 98)
    point_queue = multiprocessing.Queue()
    self.server = tire_temperature.TireSensorServer(
        'lf_tire_temp', '127.0.0.1', 27001, {}, point_queue)
    with mock.patch.object(tire_temperature, 'TireSensor') as mock_tire_sensor:
      mock_tire_sensor.return_value = mock_sensor
      client = tire_temperature.TireSensorClient('127.0.0.1', 27001)
    time.sleep(3)
    client.ReadAndSendData()
    time.sleep(3)
    point = gps_pb2.Point().FromString(point_queue.get())
    self.assertEqual(point.lf_tire_temp.inner, 188.6)
    self.assertEqual(point.lf_tire_temp.middle, 199.4)
    self.assertEqual(point.lf_tire_temp.outer, 208.4)


if __name__ == '__main__':
  absltest.main()
