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
"""Script for replaying a data log.  Super handy for development."""

import logging
import sys
import time

from absl import app
from absl import flags
import data_reader
import exit_speed
from gps import client

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')  # Dont clobber on replay.
FLAGS.set_default('led_brightness', 0.05)
flags.DEFINE_string('filepath', None, 'Path to the data file to replay')
flags.mark_flag_as_required('filepath')
flags.DEFINE_boolean('include_sleep', True,
                     'Adds delays to mimic real time replay of data.')


def ConvertPointToReport(point):
  return client.dictwrapper({
      u'lon': point.lon,
      u'lat': point.lat,
      u'mode': 3,
      u'time': point.time.ToJsonString(),
      u'alt': point.alt,
      u'speed': point.speed,
      u'class': u'TPV'})


def ReplayLog(filepath, include_sleep=False):
  """Replays data, extermely useful to LED testing.

  Args:
    filepath: A string of the path of lap data.
    include_sleep: If True replays adds sleeps to simulate how data was
                   processed in real time.

  Returns:
    A exit_speed.ExitSpeed instance that has replayed the given data.
  """
  logging.info('Replaying %s', filepath)
  points = data_reader.ReadData(filepath)
  logging.info('Number of points %d', len(points))
  if include_sleep:
    replay_start = time.time()
    time_shift = int(replay_start * 1e9 - points[0].time.ToNanoseconds())
    session_start = None
  es = exit_speed.ExitSpeed(live_data=not include_sleep)
  for point in points:
    if include_sleep:
      point.time.FromNanoseconds(point.time.ToNanoseconds() + time_shift)
      if not session_start:
        session_start = point.time.ToMilliseconds() / 1000

    report = ConvertPointToReport(point)
    es.ProcessReport(report)
    if include_sleep:
      run_delta = time.time() - replay_start
      point_delta = point.time.ToMilliseconds() / 1000 - session_start
      if run_delta < point_delta:
        time.sleep(point_delta - run_delta)

  if not include_sleep:
    time.sleep(1)
    qsize = len(es.pusher.point_queue)
    while qsize > 0:
      qsize = len(es.pusher.point_queue)
      logging.info('Queue size %s', qsize)
      time.sleep(1)  # Wait until queue is emptied by the metric pusher.
  return es


def main(unused_argv):
  ReplayLog(FLAGS.filepath, include_sleep=FLAGS.include_sleep)


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  app.run(main)
