#!/usr/bin/python3

import logging
import geohash
from multiprocessing import Process
from multiprocessing import Queue
from influxdb import InfluxDBClient


def _EmptyQueue(queue):
  """A bid odd isn't?

  My intent is to ensure we only report data on the latest point in the queue
  in case this process gets backed up.
  """
  qsize = queue.qsize()
  if qsize > 9:  # Reduce load on influxdb by only updating every 10 points.
                 # IE every 1s which is the fastest the graphs are refreshing.
    skipped_points = qsize - 9
    logging.info('Metric exporter skipped %d points', skipped_points)
    for _ in range(qsize):
      point = queue.get()
  else:
    point = queue.get()
  return point


class Pusher(object):

  def __init__(self):
    """Initializer."""
    super(Pusher, self).__init__()
    self.point_queue = Queue()
    self.lap_queue = Queue()
    self.process = Process(target=self.Loop, daemon=True)
    self.point_number = 0  # Incrementing counter of points exported.

  def GetPointMetric(self, point):
    self.point_number += 1
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
    self.influx_client.write_points(values)

  def Loop(self):
    while True:
      point = _EmptyQueue(self.point_queue)
      if self.lap_queue.qsize() > 0:
        lap = self.lap_queue.get()
      else:
        lap = None
      self.PushMetrics(point, lap)

  def Start(self):
    self.influx_client = InfluxDBClient(
        'server', 8086, 'root', 'root', 'exit_speed')
    self.process.start()


def GetMetricPusher():
  pusher = Pusher()
  pusher.Start()
  return pusher
