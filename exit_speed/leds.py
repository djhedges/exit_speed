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
"""Controls the Adafruit LEDs."""
import collections
import statistics
import time
from typing import List
from typing import Tuple

import adafruit_dotstar
import board
import numpy as np
from absl import app
from absl import flags
from absl import logging
from gps import EarthDistanceSmall
from sklearn.neighbors import BallTree

from exit_speed import exit_speed_pb2

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
flags.DEFINE_integer('min_lap_duration_sec', 60,
                     'Minimum lap duration in seconds required to be '
                     'considered a valid best lap.')
flags.DEFINE_integer('led_count', 10,
                     'Number of LEDs in the strip.')
flags.DEFINE_enum('led_direction', 'right_to_left',
                  ['left_to_right', 'right_to_left'],
                  'Physical direction of LED strip indexing from pixel 0 '
                  '(right_to_left when wires are on the right).')
flags.DEFINE_float('led_speed_step_ms', 0.5,
                   'Speed delta in m/s (~1.1 mph) per LED step from the '
                   'center of the LED strip.')


class LEDs(object):
  """Interface for controlling the changing of the LED colors."""

  def __init__(self):
    self.led_update_interval = FLAGS.led_update_interval
    self.last_led_update = time.time()
    self.dots = adafruit_dotstar.DotStar(board.SCK, board.MOSI,
                                         FLAGS.led_count,
                                         brightness=FLAGS.led_brightness)
    self.Fill((255, 0, 255), ignore_update_interval=True)  # Magenta
    self.tree = None
    self.speed_deltas = collections.deque(maxlen=FLAGS.speed_deltas)
    self.best_lap = None
    self.best_lap_duration_ns = None

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
    if ignore_update_interval:
      self.last_led_update = time.time() + additional_delay
      self.dots.fill(color)
    elif self.LedInterval(additional_delay):
      self.dots.fill(color)

  def SetLeds(self, colors: List[Tuple[int, int, int]]) -> None:
    """Sets individual LED colors if the update interval has elapsed."""
    if self.LedInterval():
      self.dots[:] = colors

  def FindNearestBestLapPoint(self,
                              point: exit_speed_pb2.Gps) -> exit_speed_pb2.Gps:
    """Returns the nearest point on the best lap to the given point."""
    neighbors = self.tree.query([[point.lat, point.lon]], k=1,
                                return_distance=False)
    index = neighbors[0][0]
    return self.best_lap[index]

  def GetLedColors(self) -> List[Tuple[int, int, int]]:
    """Returns a list of LED colors growing outward from the center split."""
    median_delta = self.GetMovingSpeedDelta()
    half_count = FLAGS.led_count // 2
    num_lit = min(half_count, int(abs(median_delta) // FLAGS.led_speed_step_ms))
    colors = [(0, 0, 0)] * FLAGS.led_count
    if median_delta > 0:
      for i in range(num_lit):
        colors[half_count - 1 - i] = (255, 0, 0)  # Red: center-left
    elif median_delta < 0:
      for i in range(num_lit):
        colors[half_count + i] = (0, 255, 0)  # Green: center-right
    if FLAGS.led_direction == 'right_to_left':
      colors.reverse()
    return colors

  def GetMovingSpeedDelta(self) -> float:
    """Returns the median speed delta over a time period based on the ring size.

    This helps smooth out the LEDs a bit so they're not so flickery by looking
    a moving median of the speed deltas.  Ring size controls how big the ring
    buffer can be, IE the number of deltas to hold on to.  At a GPS singal of
    10hz a ring size of 10 will cover a second worth of time.
    """
    return statistics.median(self.speed_deltas)

  def UpdateSpeedDeltas(self,
                        point: exit_speed_pb2.Gps,
                        best_point: exit_speed_pb2.Gps) -> float:
    speed_delta = best_point.speed_ms - point.speed_ms
    self.speed_deltas.append(speed_delta)
    return statistics.median(self.speed_deltas)

  def UpdateLeds(self, point: exit_speed_pb2.Gps) -> None:
    """Update LEDs based on speed difference to the best lap."""
    if self.tree:
      best_point = self.FindNearestBestLapPoint(point)
      self.UpdateSpeedDeltas(point, best_point)
      led_colors = self.GetLedColors()
      self.SetLeds(led_colors)

  def SetBestLap(self,
                 lap: List[exit_speed_pb2.Gps],
                 duration_ns: float) -> None:
    """Sets best lap and builds a KDTree for finding closest points."""
    if duration_ns < FLAGS.min_lap_duration_sec * 1e9:
      return
    if not self.best_lap or duration_ns < self.best_lap_duration_ns:
      minutes = duration_ns / 1e9 // 60
      seconds = (duration_ns / 1e6 % 60000) / 1000.0
      logging.info('New Best Lap %d:%.03f', minutes, seconds)
      self.best_lap = lap
      self.best_lap_duration_ns = duration_ns
      x_y_points = []
      for point in lap:
        x_y_points.append([point.lat, point.lon])
      self.tree = BallTree(np.array(x_y_points), leaf_size=30,
                           metric='pyfunc', func=EarthDistanceSmall)

  def CrossStartFinish(self) -> None:
    self.Fill((0, 0, 255),  # Blue
              additional_delay=1,
              ignore_update_interval=True)

def main(unused_argv):
  leds = LEDs()
  magenta = (255, 0, 255)
  blue = (0, 0, 255)
  red = (255, 0, 0)
  green = (0, 255, 0)
  while True:
    for color in (magenta, blue, red, green):
      leds.Fill(color, ignore_update_interval=True)
      time.sleep(1)


if __name__ == '__main__':
  app.run(main)
