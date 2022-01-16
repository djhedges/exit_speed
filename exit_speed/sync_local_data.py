#!/usr/bin/python3
# Copyright 2021 Google LLC
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
"""Syncs local data to timescale."""
import os
from typing import List
from typing import Text

import psycopg2
import tracks
from absl import app
from absl import flags
from absl import logging

from exit_speed import cleanup_timescale
from exit_speed import data_logger
from exit_speed import replay_data
from exit_speed import timescale

FLAGS = flags.FLAGS
FLAGS.set_default('data_log_path', '/tmp')  # Dont clobber on replay.
FLAGS.set_default('led_brightness', 0.05)
FLAGS.set_default('commit_cycle', 1000)

LAP_LOG_PATH = '/home/pi/lap_logs'
SELECT_SESSION = 'SELECT * FROM sessions WHERE time = %s'


def GetLocalFiles() -> List:
  data_files = []
  for carname in os.listdir(LAP_LOG_PATH):
    for filename in os.listdir(os.path.join(LAP_LOG_PATH, carname)):
      if filename.endswith('.data'):
        data_files.append(os.path.join(LAP_LOG_PATH, carname, filename))
  return data_files


def IsFileAlreadySynced(timescale_conn: psycopg2.extensions.connection,
                        filepath: Text) -> bool:
  logger = data_logger.Logger(filepath)
  first_point = None
  for point in logger.ReadProtos():
    first_point = point
    print(first_point.time.ToJsonString())
    break
  else:
    return True  # Data file has no points.
  session_time = first_point.time.ToJsonString()
  cursor = timescale_conn.cursor()
  if cursor.execute(SELECT_SESSION, (session_time,)):
    return True
  if first_point:
    _, track, _ = tracks.FindClosestTrack(first_point)
    if track.name == 'Test Parking Lot':
      return True  # Skip the test parking lot.  Mostly development files.
  return False


def SyncFile(filepath):
  replay_data.ReplayLog(filepath, include_sleep=False)


def SyncLocalData():
  timescale_conn = timescale.ConnectToDB()
  for filepath in GetLocalFiles():
    logging.info('Syncing %s', filepath)
    if not IsFileAlreadySynced(timescale_conn, filepath):
      SyncFile(os.path.join(LAP_LOG_PATH, filepath))


def main(unused_argv):
  SyncLocalData()
  cleanup_timescale.CleanupTimescale()


if __name__ == '__main__':
  app.run(main)
