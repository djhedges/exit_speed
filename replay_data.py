#!/usr/bin/python3

import logging
import time
import sys
import exit_speed
import log_files
from gps import client

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
  es = exit_speed.ExitSpeed(led_brightness=0.1)
  session = log_files.ReadLog(filepath)

  replay_start = time.time()
  session_start = session.laps[0].points[0].time.ToMilliseconds() / 1000
  replay_delta = replay_delta = replay_start - session_start

  for lap in session.laps:
    for point in lap.points:
      report = ConvertPointToReport(point)
      es.ProcessReport(report)

      run_delta = time.time() - replay_start
      point_delta = point.time.ToMilliseconds() / 1000 - session_start
      if run_delta < point_delta:
        time.sleep(point_delta - run_delta)


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  ReplayLog('testdata/data-2020-06-11T22:16:27.700Z')
