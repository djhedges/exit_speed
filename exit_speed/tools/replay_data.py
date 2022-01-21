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
import os
import time

from absl import app
from absl import flags
from absl import logging

from exit_speed import data_logger
from exit_speed import main as exit_speed_main

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')  # Dont clobber on replay.
FLAGS.set_default('led_brightness', 0.05)
flags.DEFINE_string('filepath', None, 'Path to the data file to replay')
flags.DEFINE_boolean('include_sleep', True,
                     'Adds delays to mimic real time replay of data.')


def ReplayLog(filepath, include_sleep=False):
  """Replays data, extermely useful to LED testing.

  Args:
    filepath: A string of the path of lap data.
    include_sleep: If True replays adds sleeps to simulate how data was
                   processed in real time.

  Returns:
    A exit_speed_main.ExitSpeed instance that has replayed the given data.
  """
  logging.info('Replaying %s', filepath)
  logger = data_logger.Logger(filepath)
  points = list(logger.ReadProtos())
  logging.info('Number of points %d', len(points))
  if include_sleep:
    replay_start = time.time()
    time_shift = int(replay_start * 1e9 - points[0].time.ToNanoseconds())
    session_start = None
  else:
    FLAGS.set_default('commit_cycle', 10000)
  es = exit_speed_main.ExitSpeed(live_data=not include_sleep)
  es.config['car'] = os.path.split(os.path.dirname(filepath))[1]
  for point in points:
    if include_sleep:
      point.time.FromNanoseconds(point.time.ToNanoseconds() + time_shift)
      if not session_start:
        session_start = point.time.ToMilliseconds() / 1000

    es.point = point
    es.ProcessSession()
    if include_sleep:
      run_delta = time.time() - replay_start
      point_delta = point.time.ToMilliseconds() / 1000 - session_start
      if run_delta < point_delta:
        time.sleep(point_delta - run_delta)

  if not include_sleep:
    time.sleep(1)
    qsize = len(es.timescale.point_queue)
    while qsize > 0:
      qsize = len(es.timescale.point_queue)
      logging.log_every_n_seconds(logging.INFO, 'Queue size %s', 2, qsize)
    es.timescale.stop_process_signal.value = True
    print(time.time())
    es.timescale.process.join(10)
    print(time.time())
  return es


def main(unused_argv):
  flags.mark_flag_as_required('filepath')
  ReplayLog(FLAGS.filepath, include_sleep=FLAGS.include_sleep)


if __name__ == '__main__':
  app.run(main)
