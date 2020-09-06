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
FRAME_FORMAT = {
  'lambda_16': (5, 7),  # Bytes 6 & 7
  'user_3': (13, 15),   # Bytes 13 & 14
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


def ReadSerial(ser):
  yield FindFrameStart(ser)
  while True:
    yield ser.read(FRAME_SIZE)


def GetBytes(frame, frame_key):
  low, high = FRAME_FORMAT[frame_key]
  frame_bytes = frame[low:high]
  if 'user' in frame_key:
    return int.from_bytes(frame_bytes, 'big') / 8192 * 5
  return int.from_bytes(frame_bytes, 'big')


def Lambda16ToAFR(lambda_16):
  # http://techedge.com.au/vehicle/wbo2/wblambda.htm
  # 1 = Petrol stoichiometric point.
  return ((lambda_16 / 8192) + 0.5) * 1


class WBO2(object):

  def __init__(self):
    self.afr = Value('d', 0.0)
    self.tps_voltage = Value('d', 0.0)
    self.process = Process(target=self.Loop, daemon=True)
    self.process.start()

  def Loop(self):
    with serial.Serial('/dev/ttyUSB0', 19200) as ser:
      for frame in ReadSerial(ser):
        lambda_16 = GetBytes(frame, 'lambda_16')
        self.afr.value = Lambda16ToAFR(lambda_16)
        self.tps_voltage.value = GetBytes(frame, 'user_3')


def main(unused_argv):
  ser = serial.Serial('/dev/ttyUSB0', 19200)
  for frame in ReadSerial(ser):
    lambda_16 = GetBytes(frame, 'lambda_16')
    afr = Lambda16ToAFR(lambda_16)
    tps_voltage = GetBytes(frame, 'user_3')
    print(lambda_16, afr, tps_voltage)


if __name__ == '__main__':
  app.run(main)
