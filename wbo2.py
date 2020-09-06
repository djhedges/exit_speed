#!/usr/bin/python3
"""Parser for wbo2.
https://www.wbo2.com/sw/logger.htm Frame and byte info.
https://www.wbo2.com/sw/lambda-16.htm
"""

import serial
import struct
from absl import app

FRAME_SIZE = 28


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


def main(unused_argv):
  ser = serial.Serial('/dev/ttyUSB0', 19200)
  for frame in ReadSerial(ser):
    print(frame[0], frame[1], frame[2], frame[3], frame[4])
    tick_bytes = frame[3:5]
    tick = struct.unpack(">h", tick_bytes)[0]
    print('Tick %s' % tick)
    lambda_16_bytes = frame[5:7]
    lambda_16 = struct.unpack(">h", lambda_16_bytes)[0]
    # http://techedge.com.au/vehicle/wbo2/wblambda.htm
    # 1 = Petrol stoichiometric point.
    afr = ((lambda_16 / 8192) + 0.5) * 1
    # TODO: Verify this with the car running.
    print('Lambda 16 %s, AFR %s' % (lambda_16, afr))


if __name__ == '__main__':
  app.run(main)
