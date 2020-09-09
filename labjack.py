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
"""Library for reading values from labjack."""

import time
import multiprocessing
from absl import logging
import u3


class Labjack(object):
  """Interface for the labjack DAQ."""

  def __init__(self):
    self.labjack = None
    self.labjack_timer_0 = None  # Seconds since last timer read.
    self.water_temp_voltage = multiprocessing.Value('d', 0.0)
    self.oil_pressure_voltage = multiprocessing.Value('d', 0.0)
    self.fuel_level_voltage = multiprocessing.Value('d', 0.0)
    self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    self.process.start()

  def ReadValues(self):
    """Reads the labjack voltages."""
    try:
      commands = (u3.AIN(0), u3.AIN(1), u3.AIN(2))
      ain0, ain1, ain2 = self.labjack.getFeedback(*commands)
      self.fuel_level_voltage.value = (
          self.labjack.binaryToCalibratedAnalogVoltage(
              ain0, isLowVoltage=False, channelNumber=0))
      self.water_temp_voltage.value = (
          self.labjack.binaryToCalibratedAnalogVoltage(
              ain1, isLowVoltage=False, channelNumber=1))
      self.oil_pressure_voltage.value = (
          self.labjack.binaryToCalibratedAnalogVoltage(
              ain2, isLowVoltage=False, channelNumber=2))
    except u3.LabJackException:
      logging.exception('Error reading labjack values')

  def Loop(self):
    self.labjack = u3.U3()
    while True:
      self.ReadValues()
      time.sleep(0.02)
