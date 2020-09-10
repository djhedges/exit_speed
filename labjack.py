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
from absl import app
from absl import logging
import gps_pb2
import u3


class Labjack(object):
  """Interface for the labjack DAQ."""

  def __init__(self, config):
    self.config = config
    self.u3 = None
    self.commands, self.command_point_value = self._BuildCommands()
    self.voltage_values = self._BuildValues()
    self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    self.process.start()

  def _BuildCommands(self):
    commands = []
    command_point_value = {}
    if self.config.get('labjack'):
      for input_name, point_value in self.config['labjack'].items():
        input_type = input_name[0:3]
        channel = int(input_name[-1])
        feedback_command = getattr(u3, input_type.upper())
        command = feedback_command(channel)
        commands.append(command)
        command_point_value[command] = point_value
    return commands, command_point_value

  def _BuildValues(self):
    values = {}
    if self.config.get('labjack'):
      for point_value in self.config['labjack'].values():
        values[point_value] = multiprocessing.Value('d', 0.0)
    return values

  def ReadValues(self):
    """Reads the labjack voltages."""
    try:
      results = self.u3.getFeedback(*self.commands)
      for command in self.commands:
        result = results[self.commands.index(command)]
        voltage = self.u3.binaryToCalibratedAnalogVoltage(
              result, isLowVoltage=False,
              channelNumber=command.positiveChannel)
        point_value = self.command_point_value[command]
        self.voltage_values[point_value].value = voltage
        print(result, voltage, point_value, command)
    except u3.LabJackException:
      logging.exception('Error reading labjack values')

  def Loop(self):
    self.u3 = u3.U3()
    while True:
      self.ReadValues()
