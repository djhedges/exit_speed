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
from absl import logging
import u3


class Labjack(object):
  """Interface for the labjack DAQ."""

  def __init__(self, config, start_process=True):
    self.config = config
    self.u3 = None
    self.commands, self.command_proto_field = self._BuildCommands()
    self.voltage_values = self._BuildValues()
    if start_process:
      self.process = multiprocessing.Process(target=self.Loop, daemon=True)
      self.process.start()

  def _BuildCommands(self):
    """Builds the list of feedback commands to send to the labjack device."""
    commands = []
    command_proto_field = {}
    if self.config.get('labjack'):
      for input_name, proto_field in self.config['labjack'].items():
        input_type = input_name[0:3]
        channel = int(input_name[-1])
        feedback_command = getattr(u3, input_type.upper())
        command = feedback_command(channel)
        commands.append(command)
        command_proto_field[command] = proto_field
    return commands, command_proto_field

  def _BuildValues(self):
    values = {}
    if self.config.get('labjack'):
      for proto_field in self.config['labjack'].values():
        values[proto_field] = multiprocessing.Value('d', 0.0)
    return values

  def ReadValues(self):
    """Reads the labjack voltages."""
    try:
      results = self.u3.getFeedback(*self.commands)
      for command in self.commands:
        result = results[self.commands.index(command)]
        voltage = self.u3.binaryToCalibratedAnalogVoltage(
            result,
            isLowVoltage=False,
            channelNumber=command.positiveChannel)
        proto_field = self.command_proto_field[command]
        self.voltage_values[proto_field].value = voltage
    except u3.LabJackException:
      logging.exception('Error reading labjack values')

  def Loop(self):
    self.u3 = u3.U3()
    while True:
      self.ReadValues()
