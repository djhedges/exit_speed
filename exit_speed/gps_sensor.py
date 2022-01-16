#!/usr/bin/python3
# Copyright 2022 Google LLC
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
"""GPS sensor."""
import geohash
import gps
from absl import app

from exit_speed import gps_pb2
from exit_speed import sensor

REPORT_REQ_FIELDS = ('lat', 'lon', 'time', 'speed')


class GPS(object):
  """Reads data from the GPS sensor."""

  def __init__(self, gpsd: gps.gps=None):
    self._last_gps_report_time = None  # Used to avoid duplicate GPS reports.
    self.gpsd = gpsd or gps.gps(mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)

  def CheckReportFields(self, report: gps.client.dictwrapper) -> bool:
    """Verifies required report fields are present."""
    for field in REPORT_REQ_FIELDS:
      if not report.get(field):
        return False
    return True

  def GetReport(self) -> gps.client.dictwrapper:
    report = self.gpsd.next()
    if (report.get('class') == 'TPV' and self.CheckReportFields(report)):
      if (not self._last_gps_report_time or
          self._last_gps_report_time != report.time):
        self._last_gps_report_time = report.time
        return report


class GPSProcess(sensor.SensorBase):
  """Populates the SensorBase.point_queue with GPS values per loop."""

  def Loop(self):
    """Adds point data with GPS values to point queue."""
    gps_sensor = GPS()
    while not self.stop_process_signal.value:
      report = gps_sensor.GetReport()
      if report:
        point = gps_pb2.Point()
        point.lat = report.lat
        point.lon = report.lon
        if report.get('alt'):
          point.alt = report.alt
        point.speed = report.speed
        point.geohash = geohash.encode(point.lat, point.lon)
        self.AddPointToQueue(point)


def main(unused_argv):
  gps_sensor = GPS()
  while True:
    print(gps_sensor.GetReport())


if __name__ == '__main__':
  app.run(main)
