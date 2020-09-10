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

import time
import unittest
import mock
import adafruit_dotstar
from absl.testing import absltest
import leds


class TestLEDs(unittest.TestCase):

  def setUp(self):
    self.led = leds.LEDs()
    self.led.last_led_update = time.time() - self.led.led_update_interval
    self.mock_dots = mock.create_autospec(adafruit_dotstar.DotStar,
                                          spec_set=True)
    self.led.dots = self.mock_dots

  def testLedInterval(self):
    self.assertTrue(self.led.LedInterval())
    self.assertFalse(self.led.LedInterval())
    time.sleep(self.led.led_update_interval)
    self.led.LedInterval(additional_delay=10)
    self.assertGreater(time.time() + 5, self.led.led_update_interval)

  def testFill(self):
    color = (255, 255, 255)
    self.led.Fill(color)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.led.Fill(color, ignore_update_interval=True)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.led.Fill(color, additional_delay=10, ignore_update_interval=True)
    self.assertGreater(time.time() + 5, self.led.led_update_interval)
    self.mock_dots.fill.assert_called_once_with(color)

  def testGetLedColor(self):
    red = (255, 0, 0)
    green = (0, 255, 0)
    self.led.speed_deltas = [1]
    self.assertEqual(red, self.led.GetLedColor())
    self.led.speed_deltas = [-1]
    self.assertEqual(green, self.led.GetLedColor())

  def testGetMovingSpeedDelta(self):
    self.led.speed_deltas = [-100, 5, 100]
    self.assertEqual(5, self.led.GetMovingSpeedDelta())


if __name__ == '__main__':
  absltest.main()
