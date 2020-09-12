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
"""Database schema.

CREATE TYPE track AS ENUM('Test Parking Lot',
                          'Oregon Raceway Park',
                          'Portland International Raceway',
                          'The Ridge Motorsport Park',
                          'Pacific Raceway',
                          'Spokane Raceway');
DROP TABLE points;
DROP TABLE laps;
DROP TABLE sessions;
CREATE TABLE sessions(
  id               SERIAL            PRIMARY KEY,
  time             TIMESTAMPTZ       NOT NULL,
  track            track             NOT NULL
  live_data        BOOLEAN           DEFAULT TRUE
);
CREATE TABLE laps(
  id               SERIAL            PRIMARY KEY,
  session_id       INT               REFERENCES sessions (id),
  number           INT               NOT NULL,
  duration_ms      INT
);

CREATE TABLE points (
  time                  TIMESTAMPTZ       NOT NULL,
  session_id            INT               REFERENCES sessions (id),
  lap_id                INT               REFERENCES laps (id),
  alt                   TEXT              NOT NULL,
  speed                 FLOAT             NOT NULL,
  geohash               TEXT              NOT NULL,
  elapsed_duration_ms   INT               NOT NULL,
  tps_voltage           FLOAT,
  water_temp_voltage    FLOAT,
  oil_pressure_voltage  FLOAT,
  rpm                   FLOAT,
  afr                   FLOAT,
  fuel_level_voltage    FLOAT
);
SELECT create_hypertable('points', 'time');
"""

import multiprocessing
from absl import logging
import geohash
import gps_pb2
import psycopg2


class Pusher(object):
  """Interface for publishing data to timescale."""

  def __init__(self, live_data: bool = True):
    self.live_data = live_data
    self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    self.manager = multiprocessing.Manager()
    self.timescale_conn = None
    self.session_time = None
    self.track = None
    self.session_id = None
    self.lap_number_ids = {}
    self.lap_queue = multiprocessing.Queue()
    self.lap_duration_queue = multiprocessing.Queue()
    self.point_queue = self.manager.list()  # Used as LifoQueue.
    self.lap_id_first_points = {}

  def ExportSession(self, cursor: psycopg2.extensions.cursor):
    if not self.session_id:
      insert_statement = """
      INSERT INTO sessions (time, track, live_data)
      VALUES (%s, %s, %s)
      RETURNING id
      """
      args = (self.session_time.ToJsonString(), self.track, self.live_data)
      cursor.execute(insert_statement, args)
      self.session_id = cursor.fetchone()[0]

  def ExportLap(self, cursor: psycopg2.extensions.cursor):
    """Export the lap data to timescale."""
    lap = None
    try:
      if self.lap_queue.qsize() > 0:
        lap = self.lap_queue.get()
        insert_statement = """
        INSERT INTO laps (session_id, number)
        VALUES (%s, %s)
        RETURNING id
        """
        args = (self.session_id, lap.number)
        cursor.execute(insert_statement, args)
        self.lap_number_ids[lap.number] = cursor.fetchone()[0]
    except psycopg2.Error:
      if lap:
        self.lap_queue.put(lap)  # Place lap back on queue.
      raise

  def UpdateLapDuration(self, cursor: psycopg2.extensions.cursor):
    """Exports lap duration to the Timescale backend."""
    lap_number, duration = None, None
    try:
      if self.lap_duration_queue.qsize() > 0:
        lap_number, duration = self.lap_duration_queue.get()
        update_statement = """
        UPDATE laps
        SET duration_ms = %s
        WHERE id = %s
        """
        args = (duration.ToMilliseconds(), self.lap_number_ids[lap_number])
        cursor.execute(update_statement, args)
    except psycopg2.Error:
      if lap_number:
        # Place back on queue
        self.lap_duration_queue.put((lap_number, duration))
      raise

  def GetPointFromQueue(self):
    """Returns the latest point to export metrics for."""
    while not self.point_queue:  # Queue is empty.
      pass
    return self.point_queue.pop()

  def GetElapsedTime(self, point: gps_pb2.Point, lap_id: int):
    if not self.lap_id_first_points.get(lap_id):
      self.lap_id_first_points[lap_id] = point
    first_point = self.lap_id_first_points[lap_id]
    return point.time.ToMilliseconds() - first_point.time.ToMilliseconds()

  def ExportPoint(self, cursor: psycopg2.extensions.cursor):
    """Exports point data to timescale."""
    point, lap_number = None, None
    try:
      if self.point_queue:  # Laps can be queued without points.
        point, lap_number = self.GetPointFromQueue()
        insert_statement = """
        INSERT INTO points (time, session_id, lap_id, alt, speed, geohash, elapsed_duration_ms, tps_voltage, water_temp_voltage, oil_pressure_voltage, rpm, afr, fuel_level_voltage)
        VALUES             (%s,   %s,         %s,     %s,  %s,    %s,      %s,                  %s,          %s,                 %s,                   %s,  %s,  %s)
        """
        lap_id = self.lap_number_ids.get(lap_number)
        if lap_id:
          geo_hash = geohash.encode(point.lat, point.lon)
          elapsed_duration_ms = self.GetElapsedTime(point, lap_id)
          args = (point.time.ToJsonString(),
                  self.session_id,
                  lap_id,
                  point.alt,
                  point.speed * 2.23694,  # m/s to mph,
                  geo_hash,
                  elapsed_duration_ms,
                  point.tps_voltage,
                  point.water_temp_voltage,
                  point.oil_pressure_voltage,
                  point.rpm,
                  point.afr,
                  point.fuel_level_voltage)
          cursor.execute(insert_statement, args)
        else:
          # Point arrived on the queue before the lap.  Place it back in the
          # queue and we'll try again.
          self.point_queue.append((point, lap_number))
    except psycopg2.Error:
      if point:
        self.point_queue.append((point, lap_number))  # Place back on queue
      raise

  def ConnectToDB(self):
    if not self.timescale_conn:
      self.timescale_conn = psycopg2.connect(
          'postgres://postgres:postgres@server:/exit_speed')

  def Loop(self):
    """Tries to export point data to the timescale backend."""
    while True:
      try:
        self.ConnectToDB()
        with self.timescale_conn.cursor() as cursor:
          self.ExportSession(cursor)
          self.ExportLap(cursor)
          self.UpdateLapDuration(cursor)
          self.ExportPoint(cursor)
          self.timescale_conn.commit()
      except psycopg2.Error:
        logging.exception('Error writing to timescale database')
        self.timescale_conn = None

  def Start(self, session_time, track):
    self.session_time = session_time
    self.track = track
    self.process.start()
