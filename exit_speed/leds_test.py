#!/usr/bin/python3
# Copyright 2020 Douglas Hedges
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
"""Unittests for leds_test.py"""
import collections
import sys
import time
import unittest

import fake_rpi
import mock
from absl import flags
from absl.testing import absltest

from exit_speed import exit_speed_pb2
sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO
sys.modules['smbus'] = fake_rpi.smbus # Fake smbus (I2C)
# pylint: disable=wrong-import-position
# Fixes dotstar import on Travis.
import adafruit_platformdetect
with mock.patch.object(adafruit_platformdetect, 'Detector') as mock_detector:
  mock_detector.chip.id.return_value = 'BCM2XXX'
  import adafruit_dotstar
  from exit_speed import leds
# pylint: enable=wrong-import-position

FLAGS = flags.FLAGS


class TestLEDs(unittest.TestCase):
  """LEDs unittest."""

  def setUp(self):
    super().setUp()
    mock_star = mock.create_autospec(adafruit_dotstar.DotStar)
    with mock.patch.object(adafruit_dotstar, 'DotStar') as mock_inst:
      mock_inst.return_value = mock_star
      self.leds = leds.LEDs()
    self.leds.last_led_update = time.time() - self.leds.led_update_interval
    self.mock_dots = mock.create_autospec(adafruit_dotstar.DotStar,
                                          spec_set=True)
    self.leds.dots = self.mock_dots

  def testLedInterval(self):
    self.assertTrue(self.leds.LedInterval())
    self.assertFalse(self.leds.LedInterval())
    time.sleep(self.leds.led_update_interval)
    self.leds.LedInterval(additional_delay=10)
    self.assertGreater(self.leds.last_led_update, time.time() + 5)

  def testFill(self):
    color = (255, 255, 255)
    self.leds.Fill(color)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.leds.Fill(color, ignore_update_interval=True)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.leds.Fill(color, additional_delay=10, ignore_update_interval=True)
    self.assertGreater(self.leds.last_led_update, time.time() + 5)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.leds.Fill(color)
    self.mock_dots.fill.assert_not_called()

  def testSetLeds(self):
    colors = [(0, 255, 0)] * 10
    self.leds.SetLeds(colors)
    self.mock_dots.__setitem__.assert_called_once_with(slice(None), colors)
    self.mock_dots.reset_mock()

    self.leds.SetLeds(colors)
    self.mock_dots.__setitem__.assert_not_called()

  def testFindNearestBestLapPoint(self):
    lap = []
    lap.append(exit_speed_pb2.Gps(lat=1, lon=1))
    lap.append(exit_speed_pb2.Gps(lat=5, lon=5))
    lap.append(exit_speed_pb2.Gps(lat=20, lon=20))

    self.leds.SetBestLap(lap, 90 * 1e9)  # Build the tree.
    point = exit_speed_pb2.Gps(lat=4, lon=4)
    nearest = self.leds.FindNearestBestLapPoint(point)
    self.assertEqual(nearest.lat, 5)
    self.assertEqual(nearest.lon, 5)

  def testGetLedColors(self):
    off = (0, 0, 0)
    red = (255, 0, 0)
    green = (0, 255, 0)

    # Deadband (|median_delta| < 0.5): all off.
    self.leds.speed_deltas.extend([0.2] * 10)
    self.assertListEqual(self.leds.GetLedColors(), [off] * 10)

    # Slower by 1.2 m/s (2 steps -> indices 5, 6 Red).
    self.leds.speed_deltas.extend([1.2] * 10)
    self.assertListEqual(
        self.leds.GetLedColors(),
        [off, off, off, off, off, red, red, off, off, off])

    # Slower by >= 2.5 m/s (capped at 5 steps -> indices 5..9 Red).
    self.leds.speed_deltas.extend([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    self.assertListEqual(
        self.leds.GetLedColors(),
        [off, off, off, off, off, red, red, red, red, red])

    # Faster by 1.2 m/s (2 steps -> indices 4, 3 Green).
    self.leds.speed_deltas.extend([-1.2] * 10)
    self.assertListEqual(
        self.leds.GetLedColors(),
        [off, off, off, green, green, off, off, off, off, off])

    # Faster by >= 2.5 m/s (capped at 5 steps -> indices 4..0 Green).
    self.leds.speed_deltas.extend([0, -1, -2, -3, -4, -5, -6, -7, -8, -9])
    self.assertListEqual(
        self.leds.GetLedColors(),
        [green, green, green, green, green, off, off, off, off, off])

    # Verify left_to_right direction and custom led_count.
    FLAGS.led_direction = 'left_to_right'
    FLAGS.led_count = 6
    self.addCleanup(setattr, FLAGS, 'led_direction', 'right_to_left')
    self.addCleanup(setattr, FLAGS, 'led_count', 10)
    self.leds.speed_deltas.extend([0.6] * 10)
    self.assertListEqual(
        self.leds.GetLedColors(),
        [off, off, red, off, off, off])

  def testGetMovingSpeedDelta(self):
    self.leds.speed_deltas = [-100, 5, 100]
    self.assertEqual(5, self.leds.GetMovingSpeedDelta())

  def testUpdateSpeedDeltas(self):
    point = exit_speed_pb2.Gps()
    point.speed_ms = 88  # m/s
    best_point = exit_speed_pb2.Gps()
    best_point.speed_ms = 87
    self.leds.UpdateSpeedDeltas(point, best_point)
    deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    deltas.append(-1.0)
    self.assertSequenceEqual(deltas, self.leds.speed_deltas)

  @mock.patch.object(leds.LEDs, 'SetLeds')
  def testUpdateLeds(self, mock_set_leds):
    lap = []
    point = exit_speed_pb2.Gps(speed_ms=88)
    lap.append(point)
    self.leds.UpdateLeds(point)
    self.assertFalse(mock_set_leds.mock_calls)  # No BallTree yet.

    self.leds.SetBestLap(lap, 90 * 1e9)  # Used to build the BallTree.
    self.leds.UpdateLeds(point)
    colors = [(0, 0, 0)] * 10
    mock_set_leds.assert_called_once_with(colors)
    deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    deltas.append(0.0)
    self.assertSequenceEqual(deltas, self.leds.speed_deltas)

  def testSetBestLap(self):
    lap = []
    lap.append(exit_speed_pb2.Gps(speed_ms=88))

    self.leds.SetBestLap(lap, 100 * 1e9)
    first_tree = self.leds.tree

    self.leds.SetBestLap(lap, 52.5 * 1e9)
    self.assertEqual(first_tree, self.leds.tree)
    self.assertEqual(100 * 1e9, self.leds.best_lap_duration_ns)

    lap = []
    lap.append(exit_speed_pb2.Gps(speed_ms=88))
    self.leds.SetBestLap(lap, 99 * 1e9)
    self.assertNotEqual(first_tree, self.leds.tree)

  @mock.patch.object(leds.LEDs, 'Fill')
  def testCrossStartFinish(self, mock_fill):
    self.leds.CrossStartFinish()
    blue = (0, 0, 255)
    mock_fill.assert_called_once_with(blue,
                                      additional_delay=1,
                                      ignore_update_interval=True)


if __name__ == '__main__':
  absltest.main()
