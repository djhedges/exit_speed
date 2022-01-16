# pytype: skip-file
#!/usr/bin/python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""CSV library for converting data from Traqmate to exit speed or vice versa."""
import csv
import datetime
import time

from exit_speed import gps_pb2
from exit_speed import main


def _ReadCsvFile(filepath):
  """Reads the given CSV file."""
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
  """Converts a Traqmate CSV file into a exit speed proto.

  Args:
    filepath: The file name and path of the Traqmate CSV file.

  Returns:
    A exit speed session proto.
  """
  es = main.ExitSpeed()
  start = time.time()
  first_elapsed = None
  for elapsed_time, json_time, lat, lon, alt, speed in _ReadCsvFile(filepath):
    point = gps_pb2.Point()
    point.lon = lon
    point.lat = lat
    point.alt = alt
    point.speed = speed
    es.ProcessReport(point)
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
  return es.session


def ConvertProtoToTraqmate(session, filepath):
  """Converts a exit speed session to the Traqmate CSV format.

  Args:
    session: A exit speed session proto.
    filepath: The file path and name of the new CSV file.
  """
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
                         'Altitude (meters)', 'Velocity (MPH)', 'Lap',
                         'RPM', 'TPS', 'Latitude Gs', 'Longitude Gs',
                         'Front Brake Pressure Voltage',
                         'Rear Brake Pressure Voltage'])
    for lap in session.laps:
      lap_num += 1
      for point in lap.points:
        elapsed_time = (point.time.ToNanoseconds() -
                        first_point.time.ToNanoseconds())
        speed = point.speed / 0.44704
        csv_writer.writerow([
            elapsed_time / 1000000000.0,
            point.lat,
            point.lon,
            point.alt,
            speed,
            lap_num,
            point.rpm,
            point.tps_voltage,
            point.accelerometer_x,
            point.accelerometer_y,
            point.front_brake_pressure_voltage,
            point.rear_brake_pressure_voltage
            ])
