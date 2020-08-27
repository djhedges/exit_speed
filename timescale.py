#!/usr/bin/python3

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
        self.timescale_conn.commit()

  def Start(self, session_time, track):
    self.session_time = session_time
    self.track = track
    self.process.start()


def GetMetricPusher(track):
  pusher = Pusher(session_time, track)
  return pusher
