#!/usr/bin/python3

import logging
import time
import sys
import exit_speed
import gps_pb2
import log_files
from gps import client
import tensorflow as tf


def ConvertPointToReport(point):
  return client.dictwrapper({
              u'lon': point.lon,
              u'lat': point.lat,
              u'mode': 3,
              u'time': point.time.ToJsonString(),
              u'alt': point.alt,
              u'speed': point.speed,
              u'class': u'TPV'})


def ReplayLog(filepath):
  replay_start = time.time()
  session_start = None
  es = exit_speed.ExitSpeed(start_speed=2.0,
                            led_brightness=0.05)
  data = tf.data.TFRecordDataset(filepath)
  for record in data:
    point = gps_pb2.Point()
    point.ParseFromString(record.numpy())
    if not session_start:
      session_start = point.time.ToMilliseconds() / 1000

    report = ConvertPointToReport(point)
    es.ProcessReport(report)
    run_delta = time.time() - replay_start
    point_delta = point.time.ToMilliseconds() / 1000 - session_start
    if run_delta < point_delta:
      time.sleep(point_delta - run_delta)


if __name__ == '__main__':
  tf.enable_eager_execution()
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  ReplayLog('testdata/data-2020-06-11T22:16:27.700Z.tfr')
