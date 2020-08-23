#!/usr/bin/python3

import csv
import datetime
import logging
import sys
import tempfile
import time
import exit_speed
import replay_data
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
    # Traqmate CSV files have data points every 0.025s where as our GPS sensor
    # will only record at 0.1s.
    if elapsed_time * 10 % 1 != 0:
      continue
    if start + elapsed_time > now:
      print(json_time, speed)
      sleep_duration = start + elapsed_time - first_elapsed - now
      if sleep_duration > 0:
        time.sleep(sleep_duration)
  return es.GetSession()


def ConvertProtoToTraqmate(session, filepath):
  first_point = session.laps[0].points[0]
  first_point_date = first_point.time.ToDatetime()
  last_point = session.laps[-1].points[-1]
  duration = last_point.time.ToSeconds() - first_point.time.ToSeconds()
  lap_num = 0
  with open(filepath, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['Format', 'Traqmate Trackvision', 'V2'])
    csv_writer.writerow(['Track', session.track])
    csv_writer.writerow(['Vehicle', 'CORRADO'])
    csv_writer.writerow(['Driver', 'DJ'])
    csv_writer.writerow(['Starting Date',
                         first_point_date.strftime('%Y/%m/%d')])
    csv_writer.writerow(['Starting Time',
                         first_point_date.strftime('%H:%M:%03S')])
    csv_writer.writerow(['Sample Rate (samps/sec)', 10])
    csv_writer.writerow(['Duration (secs)', duration])
    csv_writer.writerow(['Elapsed Time', 'Lat (Degrees)', 'Lon (Degrees)',
                         'Altitude (meters)', 'Velocity (MPH)', 'Lap'])
    for lap in session.laps:
      lap_num += 1
      for point in lap.points:
        elapsed_time = (point.time.ToNanoseconds() -
                        first_point.time.ToNanoseconds())
        speed = point.speed / 0.44704
        csv_writer.writerow([
            elapsed_time / 1000000000.0, point.lat, point.lon, point.alt, speed, lap_num])

if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  #ConvertTraqmateToProto('testdata/2019-08-18_Portland_CORRADO_DJ_R03_stripped.csv')
  _, temp_csv = tempfile.mkstemp(prefix='exit_speed_')
  print(temp_csv)
  es = replay_data.ReplayLog(
      '/home/pi/lap_logs/data-2020-07-10T18:20:00.700Z.tfr')
  session = es.GetSession()
  ConvertProtoToTraqmate(session, temp_csv)
