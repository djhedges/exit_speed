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


def PushMetrics(point, influx_client):
  values = []
  geo_hash = geohash.encode(point.lat, point.lon)
  values.append({'measurement': 'point',
                 'fields': {'alt': point.alt,
                            'speed': point.speed * 2.23694, # m/s to mph.
                           },
                 'tags': {'geohash': geo_hash}})
  influx_client.write_points(values)


def Loop(queue, influx_client):
  while True:
    point = _EmptyQueue(queue)
    PushMetrics(point, influx_client)


def GetMetricPusher():
  queue = Queue()
  influx_client = InfluxDBClient('server', 8086, 'root', 'root',
                                 'exit_speed')
  pusher = Process(target=Loop, args=(queue, influx_client), daemon=True)
  pusher.start()
  return queue, pusher, influx_client
