import serial
import string
import binascii
from absl import app
from absl import logging
from exit_speed import exit_speed_pb2
from exit_speed import sensor


def calculate_checksum(data):
    checksum = sum(data[2:])
    return checksum & 0xff


class WaveshareSerial(object):
  
  def __init__(self):
    super().__init__()
    self.ser = serial.Serial("/dev/ttyUSB0", 2000000)
    self.SetBaudRate()

  def __del__(self):
    self.ser.close()

  def SetBaudRate(self):
    set_can_baudrate = [
        0xaa,     #  0  Packet header
        0x55,     #  1  Packet header
        0x12,     #  3 Type: use variable protocol to send and receive data##  0x02- Setting (using fixed 20 byte protocol to send and receive data),   0x12- Setting (using variable protocol to send and receive data)##
        0x03,     #  3 CAN Baud Rate:  500kbps  ##  0x01(1Mbps),  0x02(800kbps),  0x03(500kbps),  0x04(400kbps),  0x05(250kbps),  0x06(200kbps),  0x07(125kbps),  0x08(100kbps),  0x09(50kbps),  0x0a(20kbps),  0x0b(10kbps),   0x0c(5kbps)##
        0x01,     #  4  Frame Type: Extended Frame  ##   0x01 standard frame,   0x02 extended frame ##
        0x00,     #  5  Filter ID1
        0x00,     #  6  Filter ID2
        0x00,     #  7  Filter ID3
        0x00,     #  8  Filter ID4
        0x00,     #  9  Mask ID1
        0x00,     #  10 Mask ID2
        0x00,     #  11 Mask ID3
        0x00,     #  12 Mask ID4
        0x00,     #  13 CAN mode:  normal mode  ##   0x00 normal mode,   0x01 silent mode,   0x02 loopback mode,   0x03 loopback silent mode ##
        0x00,     #  14 automatic resend:  automatic retransmission
        0x00,     #  15 Spare
        0x00,     #  16 Spare
        0x00,     #  17 Spare
        0x00,     #  18 Spare
    ]
    checksum = calculate_checksum(set_can_baudrate)
    set_can_baudrate.append(checksum)
    set_can_baudrate = bytes(set_can_baudrate)
    self.ser.write(set_can_baudrate)
    logging.info("CAN baud rate setting command sent.")

  def ReadFrames(self):
    strFrameType = ""
    strFrameFormat = ""
    len2 = 0
    id = 0
    while True:
        data = self.ser.read(2)
        hex_data1 = [hex(byte) for byte in data]
        if (data[0] == 0xaa) and (data[1] & 0xc0 == 0xc0):  # frame header
            len = data[1] & 0x0f
            if data[1] & 0x10 == 0x00:
                strFrameFormat = "Data Frame"
            else:
                strFrameFormat = "Remote Frame"

            if data[1] & 0x20 == 0x00:
                strFrameType = "Standard Frame"
                len2 = len + 3
            else:
                strFrameType = "Extended Frame"
                len2 = len + 5

            data2 = self.ser.read(len2)
            hex_data = [hex(byte) for byte in data2]
            hex_data1 += hex_data
            if data2[len2 - 1] == 0x55:  # end code
                if strFrameType == "Standard Frame":
                    id = data2[1]
                    id <<= 8
                    id += data2[0]
                    strId = hex(id)

                    if len > 0:
                        CanData = hex_data[2:2 + len]
                    else:
                        CanData = ["No Data"]
                else:
                    id = data2[3]
                    id <<= 8
                    id += data2[2]
                    id <<= 8
                    id += data2[1]
                    id <<= 8
                    id += data2[0]
                    strId = hex(id)
                    if len > 0:
                        CanData = hex_data[4:4 + len]
                    else:
                        CanData = ["No Data"]
                print("Receive CAN id: " + strId + " Data:", end='')
                print(CanData)
                print(strFrameType + ", " + strFrameFormat)
                yield (strId, CanData)
            else:
                logging.log_every_n_seconds(logging.DEBUG,
                                            "Receive Packet header Error")

def main(unused_argv):
  waveshare = WaveshareSerial()
  for can_id, data in waveshare.ReadFrames():
    print(can_id, data)
    break

if __name__ == '__main__':
  app.run(main) 
