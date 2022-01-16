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
import multiprocessing
import sys
import time
import traceback
from typing import Dict

import u3
from absl import logging

from exit_speed import gps_pb2
from exit_speed import sensor


class Labjack(sensor.SensorBase):
  """Interface for the labjack DAQ."""
  HIGH_VOLTAGE_CHANNELS = (0, 1, 2, 3)

  def __init__(
      self,
      config: Dict,
      point_queue: multiprocessing.Queue,
      start_process:bool=True):
    self.u3 = None
    super().__init__(config, point_queue, start_process=start_process)

  def Set5vOutput(self):
    """In our case sets DAC0 to output 5v.

    The brake pressure sensors need a 5v reference signal.
    DAC is more stable than VS.
    """
    if self.config.get('labjack'):
      if self.config['labjack'].get('dac0_5v_out'):
        dac0_register = 5000
        self.u3.writeRegister(dac0_register, 5.0)

  def ReadValues(self):
    """Reads the labjack voltages."""
    try:
      if self.config.get('labjack'):
        point = gps_pb2.Point()
        point.labjack_temp_f = (
            self.u3.getTemperature() * 9.0/5.0 - 459.67)
        for input_name, proto_field in self.config['labjack'].items():
          if input_name.startswith('ain') or input_name.startswith('fio'):
            channel = int(input_name[-1])
            # Note getFeedback(u3.AIN(4)) is reading voltage from FIO4.
            # Physically AIN4 and FIO4 are identical.  AIN is for analog input
            # and FIO is flexible input/output.
            feedback = self.u3.getFeedback(u3.AIN(channel))[0]
            is_low_voltage = channel not in self.HIGH_VOLTAGE_CHANNELS
            voltage = self.u3.binaryToCalibratedAnalogVoltage(
                feedback,
                isLowVoltage=is_low_voltage,
                channelNumber=channel)
            if input_name in self.config['labjack'].get('tick_divider_10'):
              voltage = voltage * 10
            setattr(point, proto_field, voltage)
        self.AddPointToQueue(point)
    except u3.LabJackException:
      stack_trace = ''.join(traceback.format_exception(*sys.exc_info()))
      logging.log_every_n_seconds(logging.ERROR,
                                  'Error reading labjack values\n%s',
                                  10,
                                  stack_trace)

  def Loop(self):
    self.u3 = u3.U3()
    # AIN0-3 are always analog but we need to set FIO4-7 to analog before we can
    # read voltages on these terminals.
    self.u3.configIO(FIOAnalog = 0b11111111)
    self.Set5vOutput()
    frequency_hz = int(
        self.config.get('labjack', {}).get('frequency_hz')) or 10
    while not self.stop_process_signal.value:
      cycle_time = time.time()
      self.ReadValues()
      time.sleep(sensor.SleepBasedOnHertz(cycle_time, frequency_hz))
