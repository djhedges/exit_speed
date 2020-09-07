#!/usr/bin/python3
"""Library for reading values from labjack."""

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
    self.process = multiprocessing.Process(target=self.Loop, daemon=True)
    self.process.start()

  def ReadValues(self):
    """Reads the labjack voltages."""
    try:
      commands = (u3.AIN(1), u3.AIN(2))
      ain1, ain2 = self.labjack.getFeedback(*commands)
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
