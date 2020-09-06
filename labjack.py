#!/usr/bin/python3
"""Library for reading values from labjack."""

import u3
from absl import logging
from multiprocessing import Process
from multiprocessing import Value


class Labjack(object):

  def __init__(self):
    self.labjack = None
    self.labjack_timer_0 = None  # Seconds since last timer read.
    self.water_temp_voltage = Value('d', 0.0)
    self.oil_pressure_voltage = Value('d', 0.0)
    self.process = Process(target=self.Loop, daemon=True)
    self.process.start()

  def ReadValues(self):
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
