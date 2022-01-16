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
"""Library for appending protos to a file.

Based the recommendation here.
https://developers.google.com/protocol-buffers/docs/techniques
"""
import datetime
import multiprocessing
import time
from typing import Dict

from exit_speed import gps_pb2

def SleepBasedOnHertz(cycle_time: float, frequency_hz: float) -> float:
  """Calculates how to sleep to maintain the expected cycle reading.

  This is useful for sensor which are polled or have high rates.

  Args;
    cycle_time: A float of the time in the loop before the sensor reading.
    frequency_hz: The target frequency reading we're aiming for.
                  See https://docs.python.org/3/tutorial/floatingpoint.html for
                  an explanation as to why this will be slightly off.

  Returns:
    A float duration in seconds.
  """
  seconds = 1.0 / frequency_hz
  sleep = seconds - (time.time() - cycle_time)
  if sleep < 0:
    return 0
  return sleep

class SensorBase(object):
  """Base class for sensor processes."""

  def __init__(
      self,
      config: Dict,
      point_queue: multiprocessing.Queue,
      start_process: bool=True):
    self.config = config
    self._point_queue = point_queue
    self.stop_process_signal = multiprocessing.Value('b', False)
    if start_process:
      self._process = multiprocessing.Process(
          target=self.Loop,
          daemon=True)
      self._process.start()

  def StopProcess(self):
    """Sets the stop process signal."""
    self.stop_process_signal.value = True

  def Join(self):
    """Sends the stop process signal and joins the process until it finishes."""
    self.StopProcess()
    self._process.join()

  def AddPointToQueue(self, point: gps_pb2.Point):
    point.time.FromDatetime(datetime.datetime.now())
    self._point_queue.put(point.SerializeToString())

  def Loop(self):
    raise NotImplementedError('Subclasses should override this method.')
