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
"""Controls the Adafruit LEDs."""
import collections
import statistics
import time
from typing import Tuple

import adafruit_dotstar
import board
import numpy as np
from absl import flags
from absl import logging
from gps import EarthDistanceSmall
from sklearn.neighbors import BallTree

from exit_speed import gps_pb2

FLAGS = flags.FLAGS
flags.DEFINE_float('led_brightness', 0.5,
                   'Percentage of how bright the LEDs are. IE 0.5 == 50%.')
flags.DEFINE_float('led_update_interval', 0.2,
                   'Limits how often the LEDs are able to change to prevent '
                   'excessive flickering.')
flags.DEFINE_integer('speed_deltas', 10,
                     'Used to smooth out GPS data.  This controls how many '
                     'recent speed deltas are stored.  50 at 10hz means a '
                     'median of the last 5 seconds is used.')


class LEDs(object):
  """Interface for controlling the changing of the LED colors."""

  def __init__(self):
    self.led_update_interval = FLAGS.led_update_interval
    self.last_led_update = time.time()
    self.dots = adafruit_dotstar.DotStar(board.SCK, board.MOSI, 10,
                                         brightness=FLAGS.led_brightness)
    self.Fill((0, 0, 255), ignore_update_interval=True)  # Blue
    self.tree = None
    self.speed_deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    self.best_lap = None

  def LedInterval(self,
                  additional_delay: float = 0) -> bool:
    """Returns True if it is safe to update the LEDs based on interval."""
    now = time.time()
    if now - self.last_led_update > self.led_update_interval:
      self.last_led_update = now + additional_delay
      return True
    return False

  def Fill(self,
           color: Tuple[int, int, int],
           additional_delay: float = 0.0,
           ignore_update_interval: bool = False) -> None:
    """Sets all of the LEDs to the specified color.

    Args:
      color: A tuple of (R, G, B) values 0-255.
      additional_delay: Adds an additional delay to the update interval.
                        This is used when crossing start/finish to set the LEDs
                        to blue for a full second.
      ignore_update_interval: If True skips the update interval check.
    """
    update = self.LedInterval(additional_delay)
    if ignore_update_interval or update:
      self.dots.fill(color)

  def FindNearestBestLapPoint(self, point: gps_pb2.Point) -> gps_pb2.Point:
    """Returns the nearest point on the best lap to the given point."""
    neighbors = self.tree.query([[point.lat, point.lon]], k=1,
                                return_distance=False)
    for neighbor in neighbors[0]:
      x = self.tree.data[:, 0][neighbor]
      y = self.tree.data[:, 1][neighbor]
      for point_b in self.best_lap.points:
        if point_b.lat == x and point_b.lon == y:
          return point_b

  def GetLedColor(self) -> Tuple[int, int, int]:
    median_delta = self.GetMovingSpeedDelta()
    if median_delta > 0:
      return (255, 0, 0)  # Red
    return (0, 255, 0)  # Green

  def GetMovingSpeedDelta(self) -> float:
    """Returns the median speed delta over a time period based on the ring size.

    This helps smooth out the LEDs a bit so they're not so flickery by looking
    a moving median of the speed deltas.  Ring size controls how big the ring
    buffer can be, IE the number of deltas to hold on to.  At a GPS singal of
    10hz a ring size of 10 will cover a second worth of time.
    """
    return statistics.median(self.speed_deltas)

  def UpdateSpeedDeltas(self,
                        point: gps_pb2.Point,
                        best_point: gps_pb2.Point) -> float:
    speed_delta = best_point.speed - point.speed
    self.speed_deltas.append(speed_delta)
    return statistics.median(self.speed_deltas)

  def UpdateLeds(self, point: gps_pb2.Point) -> None:
    """Update LEDs based on speed difference to the best lap."""
    if self.tree:
      best_point = self.FindNearestBestLapPoint(point)
      self.UpdateSpeedDeltas(point, best_point)
      led_color = self.GetLedColor()
      self.Fill(led_color)

  def SetBestLap(self, lap: gps_pb2.Lap) -> None:
    """Sets best lap and builds a KDTree for finding closest points."""
    if (not self.best_lap or
        lap.duration.ToNanoseconds() < self.best_lap.duration.ToNanoseconds()):
      minutes = lap.duration.ToSeconds() // 60
      seconds = (lap.duration.ToMilliseconds() % 60000) / 1000.0
      logging.info('New Best Lap %d:%.03f', minutes, seconds)
      self.best_lap = lap
      x_y_points = []
      for point in lap.points:
        x_y_points.append([point.lat, point.lon])
      self.tree = BallTree(np.array(x_y_points), leaf_size=30,
                           metric='pyfunc', func=EarthDistanceSmall)

  def CrossStartFinish(self) -> None:
    self.Fill((0, 0, 255),  # Blue
              additional_delay=1,
              ignore_update_interval=True)
