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
"""GoPro camera control over bluetooth.

Note enabling WiFi generates more heat and battery consummation.

Some interesting links:
  https://gethypoxic.com/blogs/technical/gopro-hero5-interfaces
  https://github.com/KonradIT/goprowifihack/blob/master/Bluetooth/Platforms/RaspberryPi.md
  https://github.com/KonradIT/gopro-ble-py
"""

import time
from absl import app
from absl import flags
import pygatt

FLAGS = flags.FLAGS
flags.DEFINE_integer('min_speed_mph', 30,
                     'Minimum speed before the camera is activated.')
flags.DEFINE_integer('stop_recording_duration_minutes', 5,
                     'If speed is below the min_speed_mph value for this '
                     'duration shutoff the recording.  Hopefully we turn off '
                     'the camera before the car is shutoff.')

COMMAND_UUID = 'b5f90072-aa8d-11e3-9046-0002a5d5c51b'
RECORD_START = bytearray(b'\x03\x01\x01\x01')
RECORD_STOP = bytearray(b'\x03\x01\x01\x00')


class GoPro(object):
  """Starts/stops the GoPro recording."""

  def __init__(self, mac_address):
    self.adapter = pygatt.GATTToolBackend()
    self.adapter.start()
    self.camera = self.adapter.connect(
        mac_address, address_type=pygatt.BLEAddressType.random)
    self.recording = False
    # Last time in UTC seconds that the min_speed_mph threshold was surpassed.
    self.last_speed_threshold = None

  def _WriteCmd(self, command):
    self.camera.char_write(COMMAND_UUID, command)

  def Start(self):
    self._WriteCmd(RECORD_START)

  def Stop(self):
    self._WriteCmd(RECORD_STOP)

  def ProcessPoint(self, point):
    """Start/Stop recording based on point's speed."""
    if point.speed > FLAGS.min_speed_mph:
      self.last_speed_threshold = point.time.ToSeconds()

    # Convert point.speed to MPH.
    if (self.recording and
        point.speed < FLAGS.min_speed_mph and
        self.last_speed_threshold and
        point.time.ToSeconds() - self.last_speed_threshold >
        FLAGS.stop_recording_duration_minutes * 60):
      self.Stop()
      self.recording = False
    if not self.recording and point.speed > FLAGS.min_speed_mph / 2.23694:
      self.Start()
      self.recording = True



def main(unused_argv):
  gopro = GoPro()
  gopro.Start()
  time.sleep(5)
  gopro.Stop()


if __name__ == '__main__':
  app.run(main)
