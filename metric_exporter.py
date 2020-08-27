#!/usr/bin/python3

import logging
import queue
import geohash
import psycopg2
from multiprocessing import Process
from multiprocessing import Queue


class Pusher(object):

  def __init__(self, track):
    """Initializer."""
    super(Pusher, self).__init__()
    self.track = track
    self.point_queue = Queue()
    self.backlog_point_queue = queue.LifoQueue()
    self.lap_queue = Queue()
    self.process = Process(target=self.Loop, daemon=True)
    self.points_exported = 0  # Incrementing counter of points exported.
    self.points_skipped = 0
    self.first_point = None
    self.first_point_time = None
    self.current_lap = 1

  def GetPointFromQueue(self):
    """Returns the latest point to export metrics for.

    This methods clears the queue based on the current size and then blocks and
    returns the next point that is added.
    """
    qsize = self.point_queue.qsize()
    for _ in range(qsize):
      self.points_skipped += 1
      _ = self.point_queue.get()
    return self.point_queue.get()

  def ExportProcMetrics(self):
    with self.timescale_conn.cursor() as cursor:
        insert_statement = """
        INSERT INTO metric_exporter (time, points_exported, points_skipped)
        VALUES (NOW(), %s, %s)
        """
        args = (self.points_exported, self.points_skipped)
        cursor.execute(insert_statement, args)

  def ExportPointMetric(self, point):
    self.points_exported += 1
    geo_hash = geohash.encode(point.lat, point.lon, precision=24)
    with self.timescale_conn.cursor() as cursor:
      if point.lap_number != self.current_lap or not self.first_point_time:
        self.first_point = point
        self.first_point_time = point.time.ToMilliseconds()
        self.current_lap = point.lap_number
        insert_statement = """
        INSERT INTO laps (time, lap_number, track)
        VALUES (%s, %s, %s)
        """
        args = (self.first_point.time.ToJsonString(),
                point.lap_number,
                self.track)
        cursor.execute(insert_statement, args)

      elapsed_duration = point.time.ToMilliseconds() - self.first_point_time
      # timescale
      insert_statement = """
      INSERT INTO points (time, lap_time, alt, speed, geohash, elapsed_duration)
      VALUES (%s, %s, %s, %s, %s, %s)
      """
      args = (point.time.ToJsonString(),
              self.first_point.time.ToJsonString(),
              point.alt,
              point.speed * 2.23694, # m/s to mph.
              geo_hash,
              elapsed_duration)
      cursor.execute(insert_statement, args)

  def ExportLapMetric(self, point, lap):
    if lap:
      lap_point = lap.points[0]
      with self.timescale_conn.cursor() as cursor:
        insert_statement = """
        UPDATE laps
        SET duration_ms = %s
        WHERE time = %s
        """
        args = (lap.duration.ToMilliseconds(),
                lap_point.time.ToJsonString())
        cursor.execute(insert_statement, args)

  def PushMetrics(self, point, lap):
    self.ExportPointMetric(point)
    self.ExportLapMetric(point, lap)
    self.ExportProcMetrics()
    self.timescale_conn.commit()

  def Loop(self):
    while True:
      if self.lap_queue.qsize() > 0:
        lap = self.lap_queue.get()
      else:
        lap = None
      point = self.GetPointFromQueue()
      self.PushMetrics(point, lap)

  def Start(self):
    self.timescale_conn = psycopg2.connect(
        'postgres://postgres:postgres@server:/exit_speed')
    self.process.start()


def GetMetricPusher(track):
  pusher = Pusher(track)
  pusher.Start()
  return pusher
