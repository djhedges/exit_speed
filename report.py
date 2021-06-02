#!/usr/bin/python3
# Copyright 2021 Google LLC
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
"""Generate a PDF report using seaborn."""

from absl import app
from absl import flags
from matplotlib.backends.backend_pdf import PdfPages
import gps_pb2
import common_lib
import timescale
import tracks
import attr
import matplotlib
import pandas
import psycopg2
import seaborn

FLAGS = flags.FLAGS


def LabelLaps(row, suffix=''):
  minutes = row.lap_duration_ms // 60000
  seconds = (row.lap_duration_ms - minutes * 60000) / 1000
  return '%d:%0.02f Lap %d %s' % (minutes, seconds, row.lap_number, suffix)


def PointsNearTurn(row, turn):
  point = gps_pb2.Point()
  point.lat = row.lat
  point.lon = row.lon
  turn_point = gps_pb2.Point()
  turn_point.lat = turn.lat
  turn_point.lon = turn.lon
  return common_lib.PointDelta(point, turn_point)


def ApplyTurnDistance(data, turn, report_range):
  key = 't%s_distance' % turn.number
  data[key] = data.apply(
      PointsNearTurn, axis=1, turn=turn)
  return data[data[key] < report_range]


def FindClosestTrack(data):
  point = gps_pb2.Point()
  point.lat = data['lat'].iloc[0]
  point.lon = data['lon'].iloc[0]
  _, track, _ = tracks.FindClosestTrack(point)
  return track


@attr.s
class Report(object):
  conn = attr.ib(type=psycopg2.extensions.connection)

  def GetSingleLapData(self, session_id, lap_id):
    select_statement = """
      SELECT
        laps.number AS lap_number,
        laps.duration_ms AS lap_duration_ms,
        elapsed_duration_ms,
        lat,
        lon,
        tps_voltage,
        rpm,
        oil_pressure_voltage,
        speed
      FROM POINTS
      JOIN laps ON points.lap_id = laps.id
      JOIN sessions ON laps.session_id = sessions.id
      WHERE sessions.id = %s AND
      lap_id = %s
      ORDER BY points.time
      """
    return pandas.io.sql.read_sql(
        select_statement,
        self.conn,
        params=(session_id,lap_id))

  def FindLastThreeBestLaps(self):
    select_last_session = """
    SELECT sessions.id FROM sessions
    JOIN laps ON sessions.id = laps.session_id
    WHERE laps.duration_ms IS NOT NULL
    ORDER BY sessions.id DESC LIMIT 1;
    """
    data_frames = []
    with self.conn.cursor() as cursor:
      cursor.execute(select_last_session)
      self.last_session_id = cursor.fetchone()[0]

    select_best_three = """
    SELECT laps.id FROM sessions
    JOIN laps ON sessions.id = laps.session_id
    WHERE session_id = %s AND
      laps.duration_ms IS NOT NULL
    ORDER BY laps.duration_ms LIMIT 3;
    """
    with self.conn.cursor() as cursor:
      cursor.execute(select_best_three, (self.last_session_id,))
      for lap_id in cursor.fetchall():
        data_frames.append(self.GetSingleLapData(self.last_session_id, lap_id))
    return pandas.concat(data_frames)

  def FindPersonalBest(self):
    return self.GetSingleLapData(1360, 244457)


  def PlotOilPressure(self, data):
    fig, ax = matplotlib.pyplot.subplots()
    ax.set_title('Oil Pressure Scatter (whole lap)')
    seaborn.scatterplot(
        x='rpm',
        y='oil_pressure_voltage',
        hue='label',
        data=data)
    self.pdf.savefig(fig)

  def Plot(self, data, turn, y,
           x='elapsed_duration_ms', hue='label', sort=False):
    fig, ax = matplotlib.pyplot.subplots()
    ax.set_title('Turn %s %s' % (turn.number, y))
    seaborn.lineplot(
        y=y,
        x=x,
        hue=hue,
        sort=sort,
        data=data)
    self.pdf.savefig(fig)

  def Run(self):
    data = self.FindLastThreeBestLaps()
    data['label'] = data.apply(LabelLaps, axis=1)
    pob_data = self.FindPersonalBest()
    pob_data['label'] = pob_data.apply(LabelLaps, axis=1, suffix=' *PoB')
    data = pandas.concat((pob_data, data))
    matplotlib.use('pdf')
    seaborn.set_style('darkgrid')
    track = FindClosestTrack(data)
    with PdfPages('/tmp/test.pdf') as self.pdf:
      self.PlotOilPressure(data)
      for turn in track.turns:
        turn_data = ApplyTurnDistance(data, turn, turn.report_range)
        self.Plot(turn_data, turn, 'lat', x='lon')
        self.Plot(turn_data, turn, 'tps_voltage')
        self.Plot(turn_data, turn, 'speed')


def main(unused_argv):
  with timescale.ConnectToDB() as conn:
    report = Report(conn)
    report.Run()


if __name__ == '__main__':
  app.run(main)
