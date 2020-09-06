#!/usr/bin/python3
"""Parser for wbo2.
https://www.wbo2.com/sw/logger.htm Frame and byte info.
https://www.wbo2.com/sw/lambda-16.htm
"""

import serial
import struct
from absl import app
from multiprocessing import Process
from multiprocessing import Value


FRAME_SIZE = 28
# {'frame_type': (slice_left, slice_right)}
FRAME_FORMAT = {
  'header':         (0, 2),   # Bytes 1 & 2
  'sequence':       (2, 3),   # Byte 3
  'tick':           (3, 5),   # Bytes 4 & 5
  'lambda_16':      (5, 7),   # Bytes 6 & 7
  'ipx':            (7, 9),   # Bytes 8 & 9
  'user_1':         (9, 11),  # Bytes 10 & 11
  'user_2':         (11, 13), # Bytes 11 & 13
  'user_3':         (13, 15), # Bytes 13 & 14
  'thermocouple_1': (15, 17), # Bytes 16 & 17
  'thermocouple_2': (17, 19), # Bytes 18 & 19
  'thermocouple_3': (19, 21), # Bytes 20 & 21
  'thermistor':     (21, 23), # Bytes 22 & 23
  'rpm_count':      (23, 25), # Bytes 24 & 25
  'status':         (25, 27), # Bytes 26 & 27
  'crc':            (27, 28), # Byte 28
}


def FindFrameStart(ser):
  while True:
    header_byte_1 = None
    header_byte_2 = None
    b = ser.read()
    if b[0] == 0x5a:
      header_byte_1 = b
    if header_byte_1:
      b = ser.read()
      if b[0] == 0xa5:
        header_byte_2 = b
      else:
        header_byte_1 = None  # Reset, perhaps another byte was set to 0x5a.
    if header_byte_1 and header_byte_2:
      return header_byte_1 + header_byte_2 + ser.read(FRAME_SIZE - 2)


def CheckFrame(frame):
  return sum(frame) & 0b11111111 == 0xFF


def ReadSerial(ser):
  yield FindFrameStart(ser)
  while True:
    frame = ser.read(FRAME_SIZE)
    if CheckFrame(frame):
      yield frame


def GetBytes(frame, frame_key):
  low, high = FRAME_FORMAT[frame_key]
  frame_bytes = frame[low:high]
  if 'user' in frame_key:
    return int.from_bytes(frame_bytes, 'big') / 8184 * 5
  elif 'thermocouple' in frame_key:
    return int.from_bytes(frame_bytes, 'big') / 1023 * 5 / 101
  return int.from_bytes(frame_bytes, 'big')


def Lambda16ToAFR(lambda_16):
  # http://techedge.com.au/vehicle/wbo2/wblambda.htm
  # 1 = Petrol stoichiometric point.
  return ((lambda_16 / 8192) + 0.5) * 1


def RPMCountToRPM(rpm_count):
  if rpm_count:
    us_between_pulse = rpm_count * 5
    minute = 60 * 10 ** 6  # 60 seconds > microseconds
    return minute / us_between_pulse / 3  # VR6 3 sparks per revolution.
  return 0


class WBO2(object):

  def __init__(self):
    self.afr = Value('d', 0.0)
    self.tps_voltage = Value('d', 0.0)
    self.rpm = Value('i', 0)
    self.process = Process(target=self.Loop, daemon=True)
    self.process.start()

  def Loop(self):
    with serial.Serial('/dev/ttyUSB0', 19200) as ser:
      for frame in ReadSerial(ser):
        lambda_16 = GetBytes(frame, 'lambda_16')
        self.afr.value = Lambda16ToAFR(lambda_16)
        self.tps_voltage.value = GetBytes(frame, 'user_3')
        rpm_count = GetBytes(frame, 'rpm_count')
        self.rpm = RPMCountToRPM(rpm_count)


def main(unused_argv):
  ser = serial.Serial('/dev/ttyUSB0', 19200)
  for frame in ReadSerial(ser):
    lambda_16 = GetBytes(frame, 'lambda_16')
    afr = Lambda16ToAFR(lambda_16)
    tps_voltage = GetBytes(frame, 'user_3')
    rpm_count = GetBytes(frame, 'rpm_count')
    print(RPMCountToRPM(rpm_count))


if __name__ == '__main__':
  app.run(main)
