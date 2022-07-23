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
import os
import time
from absl import flags
from absl import logging
from google.protobuf import any_pb2
from typing import Dict

from exit_speed import data_logger
from exit_speed import exit_speed_pb2
from exit_speed import postgres

FLAGS = flags.FLAGS
flags.DEFINE_string('data_log_path', '/home/pi/lap_logs',
                    'The directory to save data and logs.')


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
  PROTO_CLASS = None

  def __init__(
      self,
      session_time: datetime.datetime,
      config: Dict,
      point_queue: multiprocessing.Queue,
      start_process: bool=True):
    self.session_time = session_time
    self.config = config
    self._point_queue = point_queue
    self.stop_process_signal = multiprocessing.Value('b', False)
    self.data_logger = None # pytype: Optional[data_logger.Logger]
    if self.PROTO_CLASS:
      self.postgres = postgres.Postgres(self.PROTO_CLASS,
                                        start_process=start_process)
    if start_process:
      self._process = multiprocessing.Process(
          target=self.Loop,
          daemon=True)
      self._process.start()

  def _InitializeDataLogger(self, proto: any_pb2.Any):
    file_prefix = GetLogFilePrefix(self.session_time, self, proto)
    logging.info('Logging data to %s', file_prefix)
    self.data_logger = data_logger.Logger(file_prefix, proto_class=proto)

  def StopProcess(self):
    """Sets the stop process signal."""
    self.stop_process_signal.value = True

  def Join(self):
    """Sends the stop process signal and joins the process until it finishes."""
    self.StopProcess()
    self._process.join()

  def AddPointToQueue(self, point: exit_speed_pb2.Gps):
    point.time.FromDatetime(datetime.datetime.utcnow())
    self.LogMessage(point)
    self._point_queue.put(point.SerializeToString())

  def LogMessage(self, proto: any_pb2.Any):
    if not self.data_logger:
      self._InitializeDataLogger(proto)
    self.data_logger.WriteProto(proto)

  def LogAndExportProto(self, proto: any_pb2.Any):
    proto.time.FromDatetime(datetime.datetime.utcnow())
    self.LogMessage(proto)
    self.postgres.AddProtoToQueue(proto)

  def Loop(self):
    raise NotImplementedError('Subclasses should override this method.')


def GetLogFilePrefix(session_time: datetime.datetime,
                     sensor_instance: SensorBase,
										 proto: any_pb2.Any):
  """Formats the logging path based on sensor and the given proto."""
  current_seconds = session_time.second + session_time.microsecond / 1e6
  return os.path.join(
      FLAGS.data_log_path,
      '%s/' % sensor_instance.config.get('car', 'unknown_car'),
      '%s:%03f/' % (session_time.strftime('%Y-%m-%dT%H:%M'), current_seconds),
      '%s' % sensor_instance.__class__.__name__)
