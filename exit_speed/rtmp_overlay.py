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
"""Draws a PNG image for overlaying data on RTMP streams."""
import multiprocessing
import os
import tempfile
from typing import Dict
from typing import Text

from absl import app
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from exit_speed import gps_pb2

def _FormatLapDuration(lap_duration_ms: float) -> Text:
  minutes = lap_duration_ms // 60000
  seconds = lap_duration_ms % 60000 / 1000
  return '%d:%.03f' % (minutes, seconds)


class RTMPOverlay(object):
  """Generates a PNG image for FFmpeg to interleave with a RTMP stream."""

  def __init__(
      self,
      config: Dict,
      start_process: bool=True):
    self._config = config
    self._output_path = config.get('rtmp_overlay', {}).get('output')
    _, self._temp_output = tempfile.mkstemp(
        prefix='/tmp/ramdisk/', suffix='.png')
    config_resolution = config.get('rtmp_overlay', {}).get('resolution')
    self._resolution = tuple(int(value) for value in config_resolution)
    self._font = ImageFont.truetype(
        '/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf', 40)
    self._manager = multiprocessing.Manager()
    # TODO: Make the point queue a LIFO.
    self._point_queue = multiprocessing.Queue()
    self._lap_duration_queue = self._manager.list()
    self.stop_process_signal = multiprocessing.Value('b', False)
    self._last_speed = 0.0
    if start_process:
      self._process = multiprocessing.Process(
          target=self.Loop,
          daemon=True)
      self._process.start()

  def AddPointToQueue(self, point: gps_pb2.Point):
    self._point_queue.put(point.SerializeToString())

  def AddLapDuration(self, lap_number: int, lap_duration_ms: float):
    self._lap_duration_queue.append((lap_number, lap_duration_ms))

  def DrawSpeed(self, drw: ImageDraw.Draw):
    drw.rectangle(((0, 0),
                   (200, 50)),
                  fill=(0, 0, 0, 255))
    drw.text(
        (0, 0),
        'MPH: %s' % self._last_speed,
        font=self._font,
        fill=(0, 255, 0, 255))

  def DrawLapDuration(self, drw: ImageDraw.Draw):
    height = 125
    width = 225
    top = self._resolution[1] - height
    drw.rectangle(((0, self._resolution[1] - height),
                   (width, self._resolution[1])),
                  fill=(0, 0, 0, 255))
    index = 0
    text_height = 40
    for lap_number, lap_duration_ms in self._lap_duration_queue[-3:]:
      drw.text(
          (0, top + (text_height * index)),
          '%s  %s' % (lap_number, _FormatLapDuration(lap_duration_ms)),
          font=self._font,
          fill=(0, 255, 0, 255))
      index += 1

  def ProcessPointQueue(self):
    """Updates instance variables with point values.

    Image generation takes ~0.3 seconds and most of that time is spent
    rendering the PNG file.  This method ensures we overlaying the most recent
    data values and emptying the queue.
    """
    for _ in range(self._point_queue.qsize()):
      point = gps_pb2.Point().FromString(self._point_queue.get())
      if point.speed_mph:
        self._last_speed = point.speed_mph

  def Do(self):
    self.ProcessPointQueue()
    img = Image.new('RGBA', self._resolution, (255, 255, 255, 0))
    drw = ImageDraw.Draw(img)
    self.DrawSpeed(drw)
    self.DrawLapDuration(drw)
    img.save(self._temp_output, 'PNG')
    # TODO: Move the writes to ramdisk.
    # Atomic rename to ensure FFmpeg does not read an incomplete file.
    os.replace(self._temp_output, self._output_path)

  def Loop(self):
    while not self.stop_process_signal.value:
      self.Do()


def main(unused_argv):
  config = {'rtmp_overlay': {'output': '/tmp/ramdisk/overlay.png',
                             'resolution': [1280, 720]}}
  ro = RTMPOverlay(config, start_process=False)
  ro.AddPointToQueue(gps_pb2.Point(speed=130))
  ro.AddLapDuration(1, 90123.456)
  ro.AddLapDuration(2, 91123.456)
  ro.AddLapDuration(3, 92123.456)
  ro.AddLapDuration(4, 94123.456)
  ro.Do()


if __name__ == '__main__':
  app.run(main)
