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

import multiprocessing
import time
from absl import app
from absl import flags
from absl import logging
import pygatt

FLAGS = flags.FLAGS
flags.DEFINE_integer('min_speed_mph', 30,
                     'Minimum speed before the camera is activated.')
flags.DEFINE_integer('stop_recording_duration_minutes', 5,
                     'If speed is below the min_speed_mph value for this '
                     'duration shutoff the recording.  Hopefully we turn off '
                     'the camera before the car is shutoff.')

COMMAND_UUID = 'b5f90072-aa8d-11e3-9046-0002a5d5c51b'
MODE_VIDEO = bytearray(b'\x03\x02\x01\x00')
RECORD_START = bytearray(b'\x03\x01\x01\x01')
RECORD_STOP = bytearray(b'\x03\x01\x01\x00')


class GoPro(object):
  """Starts/stops the GoPro recording."""

  def __init__(self, mac_address, start_process=True):
    self.mac_address = mac_address
    self.latest_speed_mph = None
    self.speed_mph_queue = multiprocessing.Queue()
    self.recording = False
    # Last time in UTC seconds that the min_speed_mph threshold was surpassed.
    self.last_speed_threshold = None

    self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    if start_process:
      self.process.start()

  def ConnectToCamera(self):
    logging.info('GoPro Connecting to camera')
    self.adapter = pygatt.GATTToolBackend()
    self.adapter.start()
    self.camera = self.adapter.connect(
        self.mac_address, address_type=pygatt.BLEAddressType.random)
    self._WriteCmd(MODE_VIDEO)

  def _WriteCmd(self, command):
    self.camera.char_write(COMMAND_UUID, command)

  def Start(self):
    logging.info('GoPro Record Start')
    self._WriteCmd(RECORD_START)

  def Stop(self):
    logging.info('GoPro Record Stop')
    self._WriteCmd(RECORD_STOP)

  def KeepRecordingCheck(self):
    """Start/Stop recording based on point's speed."""
    speed = self.speed_mph_queue.get()
    if speed > FLAGS.min_speed_mph:
      self.last_speed_threshold = time.time()

    if (self.recording and
        speed < FLAGS.min_speed_mph and
        self.last_speed_threshold and
        time.time() - self.last_speed_threshold >
        FLAGS.stop_recording_duration_minutes * 60):
      self.Stop()
      self.recording = False
    if not self.recording and speed > FLAGS.min_speed_mph:
      self.Start()
      self.recording = True

  def Loop(self):
    try:
      self.ConnectToCamera()
      while True:
        self.KeepRecordingCheck()
    except pygatt.exceptions.NotConnectedError as err:
      logging.error('GoPro failed to connect to camera error:%s', err)
      time.sleep(5)
      self.Loop()  # Keep trying to connect.

  def AppendSpeed(self, speed):
    speed = 50
    # Convert GPS speed from m/s to mph.
    self.speed_mph_queue.put(speed * 2.23694)


def main(unused_argv):
  gopro = GoPro('EA:BC:1B:FB:FD:C8', start_process=False)
  gopro.ConnectToCamera()
  gopro.Start()
  time.sleep(5)
  gopro.Stop()


if __name__ == '__main__':
  app.run(main)
