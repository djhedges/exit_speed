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
"""Used to cleanup database entries created during testing."""
from absl import app
from absl import flags
from absl import logging

from exit_speed import timescale

FLAGS = flags.FLAGS
flags.DEFINE_integer('min_lap_duration_ms', 60 * 1000,
                     'Nukes laps with duration short than this value.')
flags.DEFINE_integer('max_lap_duration_ms', 60 * 1000 * 3,  # 3 mins.
                     'Nukes laps with duration short than this value.')


def NukeNonLiveData(conn):
  """Delete non live data which usually generated during testing."""
  with conn.cursor() as cursor:
    nuke_statement = """
    DELETE FROM points
    WHERE session_id IN (SELECT id FROM sessions WHERE live_data = False);
    DELETE FROM laps
    WHERE session_id IN (SELECT id FROM sessions WHERE live_data = False);
    DELETE FROM sessions
    WHERE id IN (SELECT id FROM sessions WHERE live_data = False);
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def NukeLapsWithNoDuration(conn):
  """Delete any laps without a duration.

  These are usually points logged post session in the paddock.

  Args:
    conn: A connection to the timescale backend.
  """
  with conn.cursor() as cursor:
    nuke_statement = """
    DELETE FROM points
    WHERE lap_id IN (SELECT id FROM laps WHERE duration_ms is NULL);
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)
    nuke_statement = """
    DELETE FROM laps
    WHERE duration_ms is NULL;
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def NukeLapsByDuration(conn):
  """Delete laps based on time.  These are usually traffic or the out lap."""
  with conn.cursor() as cursor:
    nuke_statement = """
    DELETE FROM points
    WHERE lap_id IN (SELECT id FROM laps
                     WHERE duration_ms < %s or duration_ms > %s);
    DELETE FROM laps
    WHERE duration_ms < %s OR duration_ms > %s;
    """
    logging.info(nuke_statement)
    args = (FLAGS.min_lap_duration_ms, FLAGS.max_lap_duration_ms,
            FLAGS.min_lap_duration_ms, FLAGS.max_lap_duration_ms)
    cursor.execute(nuke_statement, args)


def NukeHangingLaps(conn):
  """Based on prior deletes these cleans up any laps without points."""
  with conn.cursor() as cursor:
    select_statement = """
    SELECT DISTINCT(lap_id) FROM points
    """
    cursor.execute(select_statement)
    laps_to_keep = set(cursor.fetchall())
    select_statement = """
    SELECT id FROM laps
    """
    cursor.execute(select_statement)
    all_lap_ids = set(cursor.fetchall())
    hanging_lap_ids = all_lap_ids.difference(laps_to_keep)
    nuke_statement = """
    DELETE FROM laps
    WHERE id IN %s
    """
    logging.info(nuke_statement)
    if hanging_lap_ids:
      args = (tuple(hanging_lap_ids),)
      cursor.execute(nuke_statement, args)


def NukeHangingSessions(conn):
  """Based on prior deletes these cleans up any sessions without laps."""
  with conn.cursor() as cursor:
    select_statement = """
    SELECT DISTINCT(session_id) FROM laps
    """
    cursor.execute(select_statement)
    sessions_to_keep = set(cursor.fetchall())
    select_statement = """
    SELECT id FROM sessions
    """
    cursor.execute(select_statement)
    all_session_ids = set(cursor.fetchall())
    hanging_session_ids = all_session_ids.difference(sessions_to_keep)
    nuke_statement = """
    DELETE FROM sessions
    WHERE id IN %s
    """
    logging.info(nuke_statement)
    if hanging_session_ids:
      args = (tuple(hanging_session_ids),)
      cursor.execute(nuke_statement, args)


def CleanupTimescale():
  logging.info('Cleaning up Timescale')
  with timescale.ConnectToDB() as conn:
    NukeNonLiveData(conn)
    NukeLapsWithNoDuration(conn)
    NukeLapsByDuration(conn)

    # Hanging deletions should probably come last.
    NukeHangingLaps(conn)
    NukeHangingSessions(conn)
    conn.commit()


def main(unused_argv):
  CleanupTimescale()


if __name__ == '__main__':
  app.run(main)
