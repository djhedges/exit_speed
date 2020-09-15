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
"""DataLogger unittest."""

import os
import tempfile
import unittest
from absl.testing import absltest
import data_logger
import gps_pb2


class TestDataLogger(unittest.TestCase):
  """DataLogger unittest."""

  def setUp(self):
    super().setUp()
    _, self.file_prefix = tempfile.mkstemp()
    self.point = gps_pb2.Point()
    self.point.alt = 1
    self.point.speed = 1
    self.point.lat = 45.69545832462609
    self.point.lon = -121.52551179751754
    self.point.tps_voltage = 2
    self.point.water_temp_voltage = 3
    self.point.oil_pressure_voltage = 4
    self.point.rpm = 1000
    self.point.afr = 14.7
    self.point.fuel_level_voltage = 5

  def testSetFilePath(self):
    logger = data_logger.Logger(self.file_prefix)
    expected = os.path.join('%s_1.data' % self.file_prefix)
    self.assertEqual(expected , logger.file_path)

  def testGetFile(self):
    logger = data_logger.Logger(self.file_prefix)
    expected = os.path.join('%s_1.data' % self.file_prefix)
    self.assertEqual(expected , logger.file_path)
    logger.GetFile(256)
    expected = os.path.join('%s_2.data' % self.file_prefix)
    self.assertEqual(expected , logger.file_path)

  def testWriteAndReadBack(self):
    logger = data_logger.Logger(self.file_prefix)
    logger.WriteProto(self.point)
    logger.WriteProto(self.point)
    logger.current_file.flush()
    file_points = []
    for file_point in logger.ReadProtos():
      file_points.append(file_point)
    expected = [self.point, self.point]
    self.assertEqual(expected, file_points)

  def testShortWrite(self):
    logger = data_logger.Logger(self.file_prefix)
    logger.WriteProto(self.point)
    logger.WriteProto(self.point)
    logger.current_file.flush()
    with open(logger.file_path, 'rb') as temp_file:
      contents = temp_file.read()
    with open(logger.file_path, 'wb') as temp_file:
      temp_file.write(contents[:-1])

    file_points = []
    for file_point in logger.ReadProtos():
      file_points.append(file_point)
    expected = [self.point]
    self.assertEqual(expected, file_points)

  def testZeroProtoBytes(self):
    logger = data_logger.Logger(self.file_prefix)
    logger.WriteProto(self.point)
    logger.current_file.flush()
    with open(logger.file_path, 'ab') as temp_file:
      temp_file.write((data_logger.PROTO_LEN_BYTES).to_bytes(
          data_logger.PROTO_LEN_BYTES, data_logger.BYTE_ORDER))

    file_points = []
    for file_point in logger.ReadProtos():
      file_points.append(file_point)
    expected = [self.point]
    self.assertEqual(expected, file_points)

  def testMidHeader(self):
    logger = data_logger.Logger(self.file_prefix)
    logger.WriteProto(self.point)
    logger.current_file.flush()
    with open(logger.file_path, 'ab') as temp_file:
      temp_file.write((1).to_bytes(
          data_logger.PROTO_LEN_BYTES, data_logger.BYTE_ORDER))

    file_points = []
    for file_point in logger.ReadProtos():
      file_points.append(file_point)
    expected = [self.point]
    self.assertEqual(expected, file_points)


if __name__ == '__main__':
  absltest.main()
