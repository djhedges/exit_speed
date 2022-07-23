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
from exit_speed import exit_speed_pb2
from exit_speed import main as exit_speed_main

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')  # Dont clobber on replay.
FLAGS.set_default('led_brightness', 0.05)
flags.DEFINE_string('filepath', None, 'Path to the data file to replay')
flags.DEFINE_boolean('include_sleep', True,
                     'Adds delays to mimic real time replay of data.')


PREFIX_PROTO_MAP = {
    'GpsSensor': exit_speed_pb2.Gps,
}
SUBPROCESS_MAP = {
    'GpsSensor': 'gps',
}


def ReadProtos(filepath):
  protos = {}
  for file_name in os.listdir(filepath):
    for prefix, proto_class in PREFIX_PROTO_MAP.items():
      if file_name.startswith(prefix):
        logger = data_logger.Logger(os.path.join(filepath, file_name),
                                    proto_class=PREFIX_PROTO_MAP[prefix])
        protos.setdefault(prefix, []).extend(logger.ReadProtos())
  return protos


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
  prefix_protos = ReadProtos(filepath)
  for protos in prefix_protos.values():
    logging.info('Number of protos %d', len(protos))
  first_gps_point = prefix_protos['GpsSensor'][0]
  if include_sleep:
    replay_start = time.time()
    time_shift = int(replay_start * 1e9 - first_gps_point.time.ToNanoseconds())
    session_start = None
  es = exit_speed_main.ExitSpeed(live_data=not include_sleep)
  es.point = first_gps_point
  es.point_queue.put(first_gps_point.SerializeToString())
  es.InitializeSubProcesses()
  es.AddNewLap()
  for prefix, subprocess_attr in SUBPROCESS_MAP.items():
    subprocess = getattr(es, subprocess_attr)
    points = prefix_protos[prefix]
    for point in points:
      subprocess.LogAndExportProto(point)
      if include_sleep:
        point.time.FromNanoseconds(point.time.ToNanoseconds() + time_shift)
        if not session_start:
          session_start = point.time.ToMilliseconds() / 1000
      if prefix == 'GpsSensor':
        es.point = point
        es.ProcessLap()
      if include_sleep:
        run_delta = time.time() - replay_start
        point_delta = point.time.ToMilliseconds() / 1000 - session_start
        if run_delta < point_delta:
          time.sleep(point_delta - run_delta)

  if not include_sleep:
    time.sleep(1)
  qsize = es.postgres._queue.qsize()
  while qsize > 0:
    qsize = es.postgres._queue.qsize()
    logging.log_every_n_seconds(logging.INFO, 'Queue size %s', 2, qsize)
  es.postgres.stop_process_signal.value = True
  print(time.time())
  es.postgres.process.join(10)
  print(time.time())
  return es


def main(unused_argv):
  flags.mark_flag_as_required('filepath')
  ReplayLog(FLAGS.filepath, include_sleep=FLAGS.include_sleep)


if __name__ == '__main__':
  app.run(main)
