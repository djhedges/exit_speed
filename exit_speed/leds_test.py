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
"""Unittests for leds_test.py"""
import collections
import sys
import time
import unittest

import fake_rpi
import mock
from absl import flags
from absl.testing import absltest

from exit_speed import gps_pb2
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
    self.assertGreater(time.time() + 5, self.leds.led_update_interval)

  def testFill(self):
    color = (255, 255, 255)
    self.leds.Fill(color)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.leds.Fill(color, ignore_update_interval=True)
    self.mock_dots.fill.assert_called_once_with(color)
    self.mock_dots.fill.reset_mock()

    self.leds.Fill(color, additional_delay=10, ignore_update_interval=True)
    self.assertGreater(time.time() + 5, self.leds.led_update_interval)
    self.mock_dots.fill.assert_called_once_with(color)

  def testFindNearestBestLapPoint(self):
    lap = gps_pb2.Lap()
    point = lap.points.add()
    point.lat = 1
    point.lon = 1
    point = lap.points.add()
    point.lat = 5
    point.lon = 5
    point = lap.points.add()
    point.lat = 20
    point.lon = 20

    self.leds.SetBestLap(lap)  # Build the tree.
    point = gps_pb2.Point()
    point.lat = 4
    point.lon = 4
    nearest = self.leds.FindNearestBestLapPoint(point)
    self.assertEqual(nearest.lat, 5)
    self.assertEqual(nearest.lon, 5)

  def testGetLedColor(self):
    self.leds.speed_deltas.extend([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    self.assertTupleEqual(self.leds.GetLedColor(), (255, 0, 0))
    self.leds.speed_deltas.extend([0, -1, -2, -3, -4, -5, -6, -7, -8, -9])
    self.assertTupleEqual(self.leds.GetLedColor(), (0, 255, 0))
    self.leds.speed_deltas.extend([0, 1, 2, 3, 4, -5, -6, -7, -8, -9])
    self.assertTupleEqual(self.leds.GetLedColor(), (0, 255, 0))

  def testGetMovingSpeedDelta(self):
    self.leds.speed_deltas = [-100, 5, 100]
    self.assertEqual(5, self.leds.GetMovingSpeedDelta())

  def testUpdateSpeedDeltas(self):
    point = gps_pb2.Point()
    point.speed = 88  # mph
    best_point = gps_pb2.Point()
    best_point.speed = 87
    self.leds.UpdateSpeedDeltas(point, best_point)
    deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    deltas.append(-1.0)
    self.assertSequenceEqual(deltas, self.leds.speed_deltas)

  @mock.patch.object(leds.LEDs, 'Fill')
  def testUpdateLeds(self, mock_fill):
    lap = gps_pb2.Lap()
    point = lap.points.add()
    point.speed = 88  # mph
    self.leds.UpdateLeds(point)
    self.assertFalse(mock_fill.mock_calls)  # No BallTree yet.

    self.leds.SetBestLap(lap)  # Used to build the BallTree.
    self.leds.UpdateLeds(point)
    color = (0, 255, 0)  # Green
    mock_fill.assert_called_once_with(color)
    deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    deltas.append(0.0)
    self.assertSequenceEqual(deltas, self.leds.speed_deltas)

  def testSetBestLap(self):
    lap = gps_pb2.Lap()
    lap.duration.FromSeconds(100)
    point = lap.points.add()
    point.speed = 88  # mph

    self.leds.SetBestLap(lap)
    first_tree = self.leds.tree

    lap = gps_pb2.Lap()
    lap.duration.FromSeconds(99)
    point = lap.points.add()
    point.speed = 88  # mph
    self.leds.SetBestLap(lap)
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
