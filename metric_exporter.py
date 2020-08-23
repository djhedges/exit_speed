#!/usr/bin/python3

import logging
from multiprocessing import Process
from multiprocessing import Queue
from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import push_to_gateway

REGISTRY = CollectorRegistry()
METRIC_LAT = Gauge('lat', 'latitude position', registry=REGISTRY)
METRIC_LON = Gauge('lon', 'longitude position', registry=REGISTRY)
METRIC_ALT = Gauge('alt', 'altitude', registry=REGISTRY)
METRIC_SPEED = Gauge('speed', 'GPS reported speed in m/s', registry=REGISTRY)

METRIC_POINTS_SKIPPED = Counter(
  'points_skipped', 'Number of points skipped', registry=REGISTRY)


def _EmptyQueue(queue):
  """A bid odd isn't?

  My intent is to ensure we only report data on the latest point in the queue
  in case this process gets backed up.
  """
  qsize = queue.qsize()
  if qsize:
    skipped_points = qsize -1
    METRIC_POINTS_SKIPPED.inc(skipped_points)
    logging.info('Metric exporter skipped %d points', skipped_points)
    for _ in range(qsize):
      point = queue.get()
  else:
    point = queue.get()
  return point


def PushMetrics(point):
  METRIC_LAT.set(point.lat)
  METRIC_LON.set(point.lon)
  METRIC_ALT.set(point.alt)
  METRIC_SPEED.set(point.speed)
  push_to_gateway('server:9091', job='exit_speed', registry=REGISTRY)


def Loop(queue):
  while True:
    point = _EmptyQueue(queue)
    PushMetrics(point)


def GetMetricPusher():
  queue = Queue()
  pusher = Process(target=Loop, args=(queue,), daemon=True)
  pusher.start()
  return queue, pusher
