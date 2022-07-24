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
"""Unitests for import_data.py"""

import datetime
import os
import pytz
import unittest
from absl.testing import absltest

from exit_speed import import_data
from exit_speed import postgres_test_lib
from exit_speed import tracks


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'testdata/Bug/Test Parking Lot/2020-06-11T22:00:00/')


class TestPostgres(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Postgres unittests."""

  def testLoadProtos(self):
    prefix_protos = import_data.LoadProtos(DATA_DIR)
    self.assertEqual(1962, len(prefix_protos['GpsSensor']))

  def testCopyProtosToPostgres(self):
    prefix_protos = import_data.LoadProtos(DATA_DIR)
    import_data.CopyProtosToPostgres(prefix_protos)
    self.cursor.execute('SELECT count(*) FROM gps')
    self.assertEqual(1962, self.cursor.fetchone()[0])

  def testReRunMain(self):
    prefix_protos = import_data.LoadProtos(DATA_DIR)
    import_data.ReRunMain(DATA_DIR, prefix_protos['GpsSensor'])
    self.cursor.execute('SELECT * from sessions')
    db_id, time, track, car, live_data = self.cursor.fetchone()
    self.assertEqual(db_id, 1)
    #self.assertEqual(time, datetime.datetime(2020, 6, 11, 22))
    self.assertEqual(track, tracks.test_track.TestTrack.name)
    self.assertEqual(car, 'Bug')
    self.assertFalse(live_data)
    self.cursor.execute(
        'SELECT number, (end_time - start_time) as lap_duration FROM laps '
        'WHERE end_time IS NOT NULL')
    res = self.cursor.fetchall()
    # TODO(djhedges): Add a test and fix the bug with lap duration.'


if __name__ == '__main__':
  absltest.main()
