#!/usr/bin/python3

import logging
import geohash
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
METRIC_GEOHASH = Gauge('geohash', 'Geohash of the latest GPS point',
                       ['geohash', 'target'], registry=REGISTRY)
METRIC_POINTS_EXPORTED = Counter(
  'points_exported', 'Number of points exported', registry=REGISTRY)
METRIC_POINTS_SKIPPED = Counter(
  'points_skipped', 'Number of points skipped', registry=REGISTRY)


def _EmptyQueue(queue):
  """A bid odd isn't?

  My intent is to ensure we only report data on the latest point in the queue
  in case this process gets backed up.
  """
  qsize = queue.qsize()
  if qsize > 1:
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
  geo_hash = geohash.encode(point.lat, point.lon)
  METRIC_GEOHASH.labels(geohash=geo_hash, target='exit_speed').set(1)
  push_to_gateway('server:9091', job='exit_speed', registry=REGISTRY)
  METRIC_POINTS_EXPORTED.inc()


def Loop(queue):
  while True:
    point = _EmptyQueue(queue)
    PushMetrics(point)


def GetMetricPusher():
  queue = Queue()
  pusher = Process(target=Loop, args=(queue,), daemon=True)
  pusher.start()
  return queue, pusher
