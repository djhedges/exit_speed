#!/usr/bin/python3

import logging
import time
import sys
import exit_speed
import gps_pb2
import data_reader
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


def ReplayLog(filepath, include_sleep=False):
  """Replays data, extermely useful to LED testing.

  Args:
    filepath: A string of the path of lap data.
    include_sleep: If True replays adds sleeps to simulate how data was
                   processed in real time.

  Returns:
    A exit_speed.ExitSpeed instance that has replayed the given data.
  """
  logging.info(f'Replaying {filepath}')
  replay_start = time.time()
  session_start = None
  es = exit_speed.ExitSpeed(data_log_path='/tmp',  # Dont clobber on replay.
                            led_brightness=0.05)
  points = data_reader.ReadData(filepath)
  for point in points:
    if not session_start:
      session_start = point.time.ToMilliseconds() / 1000

    report = ConvertPointToReport(point)
    es.ProcessReport(report)
    run_delta = time.time() - replay_start
    point_delta = point.time.ToMilliseconds() / 1000 - session_start
  if include_sleep and run_delta < point_delta:
    time.sleep(point_delta - run_delta)
  return es


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  ReplayLog('testdata/data-2020-06-11T22:16:27.700Z.tfr')
