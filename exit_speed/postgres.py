#!/usr/bin/python3
# Copyright 2022 Google LLC
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
"""Postgres interface."""

from typing import Text
import textwrap
import psycopg2
from absl import flags
from google.protobuf import any_pb2
from exit_speed import exit_speed_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string('postgres_db_spec',
                    'postgres://exit_speed:faster@localhost:/exit_speed',
                    'Postgres URI connection string.')

ARGS_GPS = ('time', 'lat', 'lon', 'alt', 'speed')
PREPARE_GPS = textwrap.dedent("""
  PREPARE gps_insert AS
  INSERT INTO gps (time, lat, lon, alt, speed)
  VALUES ($1, $2, $3, $4, $5)
""")
INSERT_GPS = textwrap.dedent("""
  EXECUTE gps_insert ($1, $2, $3, $4, $5)
""")
ARGS_MAP = {
  exit_speed_pb2.Gps: ARGS_GPS,
}
PREPARE_MAP = {
  exit_speed_pb2.Gps: PREPARE_GPS,
}
INSERT_MAP = {
  exit_speed_pb2.Gps: INSERT_GPS,
}


def ConnectToDB() -> psycopg2.extensions.connection:
  return psycopg2.connect(FLAGS.postgres_db_spec)


def GetConnWithPointPrepare(
  prepare_statement: Text, conn: psycopg2.extensions.connection =  None):
  conn = conn or ConnectToDB()
  with conn.cursor() as cursor:
    cursor.execute(prepare_statement)
  return conn


class Postgres(object):

  def __init__(self, proto_class: any_pb2.Any, start_process: bool = True):
    """Initializer."""
    self.proto_class = proto_class
    self._postgres_conn = GetConnWithPointPrepare(
            INSERT_MAP[proto_class.__class__.__name__])
    self._proto_queue = self._manager.list()  # Used as LifoQueue.
    self.stop_process_signal = multiprocessing.Value('b', False)
    if start_process:
      self.process = multiprocessing.Process(target=self.Loop, daemon=True)
      self.process.start()

  def AddProtoToQueue(self, proto: any_pb2.Any):
    self.point_queue.append(proto)

  def ExportProto(self):
    proto = self.proto_class().FromString(self._proto_queue.pop())
    args = (getattr(proto, value) for value in ARGS_MAP[self.proto_class])
    cursor.execute(INSERT_MAP[self.proto_class])

  def Loop(self):
    """Tries to export data to the postgres backend."""
    while not self.stop_process_signal.value:
      self.ExportProto()
      logging.log_every_n_seconds(
        logging.INFO,
        'Postgres: Point queue size currently at %d.',
        10,
        len(self._proto_queue))
