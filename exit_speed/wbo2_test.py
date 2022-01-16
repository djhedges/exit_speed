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
"""Unitests for wbo2.py"""
import unittest

import mock
import serial
from absl.testing import absltest

from exit_speed import wbo2

TEST_FRAME = (b'Z\xa5\x08\x0c\xf8\x0f\xff \x00\x020\x01`\x03\xd0\x00\x15\x00'
              b'\x1a\x00 \x01\xa4\x00\x00\x03\x00i')


class TestWBO2(unittest.TestCase):
  """WBO2 unittests."""

  def setUp(self):
    super().setUp()
    self.start = 0

  def MockRead(self, size=1):
    data = TEST_FRAME[5:] + TEST_FRAME
    output = data[self.start:self.start + size]
    self.start += size
    return output

  def testFindFrameStart(self):
    mock_serial = mock.create_autospec(serial.Serial)
    mock_serial.read.side_effect = self.MockRead
    self.assertEqual(TEST_FRAME, wbo2.FindFrameStart(mock_serial))

  def testCheckFrame(self):
    self.assertTrue(wbo2.CheckFrame(TEST_FRAME))
    self.assertFalse(wbo2.CheckFrame(TEST_FRAME[:-1] + b'0x02'))

  def testReadSerial(self):
    mock_serial = mock.create_autospec(serial.Serial)
    mock_serial.read.side_effect = self.MockRead
    for frame in wbo2.ReadSerial(mock_serial):
      self.assertEqual(TEST_FRAME, frame)
      break

  def testGetBytes(self):
    self.assertEqual(0.5962854349951124, wbo2.GetBytes(TEST_FRAME, 'user_3'))
    self.assertEqual(0.0010162306553235967,
                     wbo2.GetBytes(TEST_FRAME, 'thermocouple_1'))
    self.assertEqual(3320, wbo2.GetBytes(TEST_FRAME, 'tick'))
    self.assertEqual(0, wbo2.GetBytes(TEST_FRAME, 'rpm_count'))
    self.assertEqual(14.69820556640625, wbo2.GetBytes(TEST_FRAME, 'lambda_16'))

  def testLambda16ToAFR(self):
    lambda_16 = int.from_bytes(b'\x0f\xff', 'big')
    self.assertEqual(14.69820556640625, wbo2.Lambda16ToAFR(lambda_16))

  def testRPMCountToRPM(self):
    self.assertEqual(6000, wbo2.RPMCountToRPM(1000, 4))
    self.assertEqual(4000, wbo2.RPMCountToRPM(1000, 6))

  def testGetUser3(self):
    self.assertEqual(0.5962854349951124,
            wbo2.GetBytes(TEST_FRAME, 'user_3'))


if __name__ == '__main__':
  absltest.main()
