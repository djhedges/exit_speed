#!/usr/bin/python3
"""
Database schema.

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
);
CREATE TABLE laps(
  id               SERIAL            PRIMARY KEY,
  session_id       INT               REFERENCES sessions (id),
  lap_number       INT               NOT NULL,
  duration_ms      INT
);

CREATE TABLE points (
  time                TIMESTAMPTZ       NOT NULL,
  session_id          INT               REFERENCES sessions (id),
  lap_id              INT               REFERENCES laps (id),
  alt                 TEXT              NOT NULL,
  speed               FLOAT             NOT NULL,
  geohash             TEXT              NOT NULL,
  elapsed_duration_ms INT               NOT NULL
);
SELECT create_hypertable('points', 'time');
"""

import geohash
import psycopg2
from multiprocessing import Process
from multiprocessing import Queue


class Pusher(object):

  def __init__(self):
    self.process = Process(target=self.Loop, daemon=True)
    self.timescale_conn = None
    self.session_time = None
    self.track = None
    self.session_id = None
    self.lap_number_ids = {}
    self.lap_queue = Queue()
    self.lap_duration_queue = Queue()
    self.point_queue = Queue()
    self.lap_id_first_points = {}

  def ExportSession(self, cursor):
    if not self.session_id:
      insert_statement = """
      INSERT INTO sessions (time, track)
      VALUES (%s, %s)
      RETURNING id
      """
      args = (self.session_time.ToJsonString(), self.track)
      cursor.execute(insert_statement, args)
      self.session_id = cursor.fetchone()[0]

  def ExportLap(self, cursor):
    if self.lap_queue.qsize() > 0:
      lap = self.lap_queue.get()
      insert_statement = """
      INSERT INTO laps (session_id, lap_number)
      VALUES (%s, %s)
      RETURNING id
      """
      args = (self.session_id, lap.number)
      cursor.execute(insert_statement, args)
      self.lap_number_ids[lap.number] = cursor.fetchone()[0]

  def UpdateLapDuration(self, cursor):
    if self.lap_duration_queue.qsize() > 0:
      lap_number, duration = self.lap_duration_queue.get()
      update_statement = """
      UPDATE laps
      SET duration_ms = %s
      WHERE id = %s
      """
      args = (duration.ToMilliseconds(), self.lap_number_ids[lap_number])
      cursor.execute(update_statement, args)

  def GetPointFromQueue(self):
    """Returns the latest point to export metrics for.

    This methods clears the queue based on the current size and then blocks and
    returns the next point that is added.
    """
    qsize = self.point_queue.qsize()
    for _ in range(qsize):
      _ = self.point_queue.get()
    return self.point_queue.get()

  def GetElapsedTime(self, point, lap_id):
    if not self.lap_id_first_points.get(lap_id):
      self.lap_id_first_points[lap_id] = point
    first_point = self.lap_id_first_points[lap_id]
    return point.time.ToMilliseconds() - first_point.time.ToMilliseconds()

  def ExportPoint(self, cursor):
    point = self.GetPointFromQueue()
    insert_statement = """
    INSERT INTO points (time, session_id, lap_id, alt, speed, geohash, elapsed_duration_ms)
    VALUES             (%s,   %s,         %s,     %s,  %s,    %s,      %s)
    """
    lap_id = max(self.lap_number_ids.values())
    geo_hash = geohash.encode(point.lat, point.lon)
    elapsed_duration_ms = self.GetElapsedTime(point, lap_id)
    args = (point.time.ToJsonString(), self.session_id, lap_id,
            point.alt, point.speed * 2.23694, # m/s to mph,
            geo_hash, elapsed_duration_ms)
    cursor.execute(insert_statement, args)

  def ConnectToDB(self):
    self.timescale_conn = psycopg2.connect(
        'postgres://postgres:postgres@server:/exit_speed')

  def Loop(self):
    self.ConnectToDB()
    while True:
      with self.timescale_conn.cursor() as cursor:
        self.ExportSession(cursor)
        self.ExportLap(cursor)
        self.UpdateLapDuration(cursor)
        self.ExportPoint(cursor)
        self.timescale_conn.commit()

  def Start(self, session_time, track):
    self.session_time = session_time
    self.track = track
    self.process.start()


def GetMetricPusher(track):
  pusher = Pusher(session_time, track)
  return pusher
