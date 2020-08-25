#!/usr/bin/python3

import logging
import queue
import geohash
from multiprocessing import Process
from multiprocessing import Queue
from influxdb import InfluxDBClient


class Pusher(object):

  def __init__(self):
    """Initializer."""
    super(Pusher, self).__init__()
    self.point_queue = Queue()
    self.backlog_point_queue = queue.LifoQueue()
    self.lap_queue = Queue()
    self.process = Process(target=self.Loop, daemon=True)
    self.point_exported = 0  # Incrementing counter of points exported.
    self.points_skipped = 0

  def GetPointFromQueue(self):
    """Returns the latest point to export metrics for.

    This methods clears the queue based on the current size and then blocks and
    returns the next point that is added.
    """
    qsize = self.point_queue.qsize()
    self.points_skipped += 1
    for _ in range(qsize):
      _ = self.point_queue.get()
    return self.point_queue.get()

  def GetExporterMetrcis(self):
    return {'measurement': 'metric_exporter',
            'fields': {'points_skipped': self.points_skipped,
                       'points_exported': self.point_exported,
                      },
           }

  def GetPointMetric(self, point):
    self.point_exported += 1
    geo_hash = geohash.encode(point.lat, point.lon, precision=24)
    return {'measurement': 'point',
            'fields': {'alt': point.alt,
                       'speed': point.speed * 2.23694, # m/s to mph.
                       'geohash': geo_hash,
                       'point_number': point.point_number,
                      },
            'time': point.time.ToJsonString(),
            'tags': {'lap_number': point.lap_number},
           }

  def GetLapMetric(self, point, lap):
    if lap:
      lap_point = lap.points[-1]
      milliseconds = lap.duration.ToMilliseconds()
      minutes = milliseconds // 60000
      seconds = milliseconds % 60000 / 1000
      duration = '%d:%.3f' % (minutes, seconds)
      return {'measurement': 'lap',
              'fields': {'lap_number': point.lap_number,
                         'duration': duration,
                        },
              'time': lap_point.time.ToJsonString(),
             }

  def PushMetrics(self, point, lap):
    values = []
    values.append(self.GetPointMetric(point))
    lap_metric = self.GetLapMetric(point, lap)
    if lap_metric:
      values.append(lap_metric)
    values.append(self.GetExporterMetrcis())
    self.influx_client.write_points(values)

  def Loop(self):
    while True:
      if self.lap_queue.qsize() > 0:
        lap = self.lap_queue.get()
      else:
        lap = None
      point = self.GetPointFromQueue()
      self.PushMetrics(point, lap)

  def Start(self):
    self.influx_client = InfluxDBClient(
        'server', 8086, 'root', 'root', 'exit_speed')
    self.process.start()


def GetMetricPusher():
  pusher = Pusher()
  pusher.Start()
  return pusher
