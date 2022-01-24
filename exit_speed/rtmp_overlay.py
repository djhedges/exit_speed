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

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from exit_speed import gps_pb2


class RTMPOverlay(object):
  """Generates a PNG image for FFmpeg to interleave with a RTMP stream."""

  def __init__(
      self,
      config: Dict,
      point_queue:
      multiprocessing.Queue,start_process: bool=True):
    self._config = config
    self._output_path = config.get('rtmp_overlay', {}).get('output')
    _, self._temp_output = tempfile.mkstemp(suffix='.png')
    config_resolution = config.get('rtmp_overlay', {}).get('resolution')
    self._resolution = tuple(int(value) for value in config_resolution)
    self._font = ImageFont.truetype(
        '/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf', 40)
    self._point_queue = point_queue
    self.stop_process_signal = multiprocessing.Value('b', False)
    if start_process:
      self._process = multiprocessing.Process(
          target=self.Loop,
          daemon=True)
      self._process.start()

  def AddPointToQueue(self, point: gps_pb2.Point):
    self._point_queue.put(point.SerializeToString())

  def Loop(self):
    while not self.stop_process_signal.value:
      img = Image.new('RGBA', self._resolution, (255, 255, 255, 0))
      drw = ImageDraw.Draw(img)

      point = gps_pb2.Point().FromString(self._point_queue.get())
      if point.speed:
        drw.text(
            (10, 10),
            'MPH: %s' % point.speed,
            font=self._font,
            fill=(0, 255, 0, 255))
        img.save(self._temp_output, 'PNG')
        # Atomic rename to ensure FFmpeg does not read an incomplete file.
        os.replace(self._temp_output, self._output_path)
