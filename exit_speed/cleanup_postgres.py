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
"""Used to cleanup database entries created during testing."""
from absl import app
from absl import flags
from absl import logging

from exit_speed import postgres

FLAGS = flags.FLAGS
flags.DEFINE_integer('min_lap_duration_ms', 60 * 1000,
                     'Nukes laps with duration short than this value.')
flags.DEFINE_integer('max_lap_duration_ms', 60 * 1000 * 3,  # 3 mins.
                     'Nukes laps with duration short than this value.')


def NukeNonLiveData(conn):
  """Delete non live data which usually generated during testing."""
  with conn.cursor() as cursor:
    nuke_statement = """
    WITH non_live_sessions AS (
      SELECT id, time AS start_time,
             COALESCE((SELECT MAX(end_time) FROM laps WHERE session_id = sessions.id), time + INTERVAL '24 hours') AS end_time
      FROM sessions
      WHERE live_data = False
    )
    DELETE FROM gps WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE gps.time >= non_live_sessions.start_time AND gps.time <= non_live_sessions.end_time);
    DELETE FROM accelerometer WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE accelerometer.time >= non_live_sessions.start_time AND accelerometer.time <= non_live_sessions.end_time);
    DELETE FROM gyroscope WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE gyroscope.time >= non_live_sessions.start_time AND gyroscope.time <= non_live_sessions.end_time);
    DELETE FROM labjack WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE labjack.time >= non_live_sessions.start_time AND labjack.time <= non_live_sessions.end_time);
    DELETE FROM wbo2 WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE wbo2.time >= non_live_sessions.start_time AND wbo2.time <= non_live_sessions.end_time);
    DELETE FROM ecu WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE ecu.time >= non_live_sessions.start_time AND ecu.time <= non_live_sessions.end_time);
    DELETE FROM egts WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE egts.time >= non_live_sessions.start_time AND egts.time <= non_live_sessions.end_time);
    DELETE FROM pdm WHERE EXISTS (SELECT 1 FROM non_live_sessions WHERE pdm.time >= non_live_sessions.start_time AND pdm.time <= non_live_sessions.end_time);
    
    DELETE FROM laps WHERE session_id IN (SELECT id FROM sessions WHERE live_data = False);
    DELETE FROM sessions WHERE live_data = False;
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def NukeLapsWithNoDuration(conn):
  """Delete any laps without a duration.

  These are usually points logged post session in the paddock.

  Args:
    conn: A connection to the postgres backend.
  """
  with conn.cursor() as cursor:
    nuke_statement = """
    WITH laps_no_duration AS (
      SELECT start_time, COALESCE(end_time, start_time + INTERVAL '24 hours') AS end_time
      FROM laps
      WHERE duration_ns is NULL
    )
    DELETE FROM gps WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE gps.time >= laps_no_duration.start_time AND gps.time <= laps_no_duration.end_time);
    DELETE FROM accelerometer WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE accelerometer.time >= laps_no_duration.start_time AND accelerometer.time <= laps_no_duration.end_time);
    DELETE FROM gyroscope WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE gyroscope.time >= laps_no_duration.start_time AND gyroscope.time <= laps_no_duration.end_time);
    DELETE FROM labjack WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE labjack.time >= laps_no_duration.start_time AND labjack.time <= laps_no_duration.end_time);
    DELETE FROM wbo2 WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE wbo2.time >= laps_no_duration.start_time AND wbo2.time <= laps_no_duration.end_time);
    DELETE FROM ecu WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE ecu.time >= laps_no_duration.start_time AND ecu.time <= laps_no_duration.end_time);
    DELETE FROM egts WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE egts.time >= laps_no_duration.start_time AND egts.time <= laps_no_duration.end_time);
    DELETE FROM pdm WHERE EXISTS (SELECT 1 FROM laps_no_duration WHERE pdm.time >= laps_no_duration.start_time AND pdm.time <= laps_no_duration.end_time);

    DELETE FROM laps WHERE duration_ns is NULL;
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def NukeLapsByDuration(conn):
  """Delete laps based on time.  These are usually traffic or the out lap."""
  with conn.cursor() as cursor:
    nuke_statement = """
    WITH laps_out_of_bounds AS (
      SELECT start_time, COALESCE(end_time, start_time + INTERVAL '24 hours') AS end_time
      FROM laps
      WHERE duration_ns < %s OR duration_ns > %s
    )
    DELETE FROM gps WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE gps.time >= laps_out_of_bounds.start_time AND gps.time <= laps_out_of_bounds.end_time);
    DELETE FROM accelerometer WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE accelerometer.time >= laps_out_of_bounds.start_time AND accelerometer.time <= laps_out_of_bounds.end_time);
    DELETE FROM gyroscope WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE gyroscope.time >= laps_out_of_bounds.start_time AND gyroscope.time <= laps_out_of_bounds.end_time);
    DELETE FROM labjack WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE labjack.time >= laps_out_of_bounds.start_time AND labjack.time <= laps_out_of_bounds.end_time);
    DELETE FROM wbo2 WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE wbo2.time >= laps_out_of_bounds.start_time AND wbo2.time <= laps_out_of_bounds.end_time);
    DELETE FROM ecu WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE ecu.time >= laps_out_of_bounds.start_time AND ecu.time <= laps_out_of_bounds.end_time);
    DELETE FROM egts WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE egts.time >= laps_out_of_bounds.start_time AND egts.time <= laps_out_of_bounds.end_time);
    DELETE FROM pdm WHERE EXISTS (SELECT 1 FROM laps_out_of_bounds WHERE pdm.time >= laps_out_of_bounds.start_time AND pdm.time <= laps_out_of_bounds.end_time);

    DELETE FROM laps WHERE duration_ns < %s OR duration_ns > %s;
    """
    logging.info(nuke_statement)
    args = (FLAGS.min_lap_duration_ms * 1000000, FLAGS.max_lap_duration_ms * 1000000,
            FLAGS.min_lap_duration_ms * 1000000, FLAGS.max_lap_duration_ms * 1000000)
    cursor.execute(nuke_statement, args)


def NukeHangingLaps(conn):
  """Based on prior deletes these cleans up any laps without points."""
  with conn.cursor() as cursor:
    nuke_statement = """
    DELETE FROM laps
    WHERE NOT EXISTS (
      SELECT 1 FROM gps
      WHERE gps.time >= laps.start_time
        AND gps.time <= COALESCE(laps.end_time, laps.start_time + INTERVAL '24 hours')
    )
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def NukeHangingSessions(conn):
  """Based on prior deletes this cleans up any sessions without laps."""
  with conn.cursor() as cursor:
    nuke_statement = """
    DELETE FROM sessions
    WHERE NOT EXISTS (
      SELECT 1 FROM laps WHERE laps.session_id = sessions.id
    )
    """
    logging.info(nuke_statement)
    cursor.execute(nuke_statement)


def CleanupPostgres():
  logging.info('Cleaning up Timescale')
  with postgres.ConnectToDB() as conn:
    NukeNonLiveData(conn)
    NukeLapsWithNoDuration(conn)
    NukeLapsByDuration(conn)

    # Hanging deletions should probably come last.
    NukeHangingLaps(conn)
    NukeHangingSessions(conn)
    conn.commit()


def main(unused_argv):
  CleanupPostgres()


if __name__ == '__main__':
  app.run(main)
