#!/usr/bin/python3

import csv
import datetime
import logging
import sys
import time
import exit_speed
from gps import client


def _ReadCsvFile(filepath):
  reading_header = True
  start_date = None
  start_time = None
  csv_time = None
  with open(filepath) as csv_file:
    for row in csv.reader(csv_file, delimiter=','):
      if not reading_header:
        elapsed_time = row[3]
        lat = row[4]
        lon = row[5]
        alt = row[8]
        mph = row[13]
        time_str = '%s-%s' % (start_date.strip(), start_time.strip())
        csv_time = datetime.datetime.strptime(time_str, '%d/%m/%Y-%H:%M:%S.%f')
        csv_time += datetime.timedelta(seconds=float(elapsed_time.strip()))
        json_time = csv_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        speed = float(mph.strip()) * 0.44704  # m/s
        lat = float(lat.strip())
        lon = float(lon.strip())
        alt = float(alt.strip())
        yield elapsed_time, json_time, lat, lon, alt, speed
      if row[0].startswith('GPS Reading'):
        reading_header = False
      if row[0].startswith('Starting Date'):
        start_date = row[1]
      if row[0].startswith('Starting Time'):
        start_time = row[1]

def ConvertTraqmateToProto(filepath):
  es = exit_speed.ExitSpeed(led_brightness=0.05)
  start = time.time()
  first_elapsed = None
  for elapsed_time, json_time, lat, lon, alt, speed in _ReadCsvFile(filepath):
    report = client.dictwrapper({
              u'lon': lon,
              u'lat': lat,
              u'mode': 3,
              u'time': json_time,
              u'alt': alt,
              u'speed': speed,
              u'class': u'TPV'})
    es.ProcessReport(report)
    now = time.time()
    elapsed_time = float(elapsed_time)
    if not first_elapsed:
      first_elapsed = elapsed_time
    if start + elapsed_time > now:
      print(json_time, speed)
      sleep_duration = start + elapsed_time - first_elapsed - now
      if sleep_duration > 0:
        time.sleep(sleep_duration)


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  ConvertTraqmateToProto('testdata/2019-08-18_Portland_CORRADO_DJ_R03_stripped.csv')
