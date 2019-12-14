#! /usr/bin/python
#
# I did finally get this to change the GPS refresh rate
# and then found out that Ublox made this awesome windows
# software called Ucenter which lets you save changes
# like this to NVRAM.

import serial
from scapy.all import ByteEnumField
from scapy.all import ByteField
from scapy.all import Packet
from scapy.all import XByteField
from scapy.all import XLEShortField
from scapy.all import XShortField
from scapy.compat import raw


class UbxCfgGRate(Packet):
  name = 'UBX-CFG-RATE'
  fields_desc = [
    XShortField('preamble', 0xB562),
    XByteField('message_class', 0x06),
    XByteField('message_id', 0x08),
    XLEShortField('length', 0x06),
    ByteField('measRate', 100),  # 10hz
    ByteField('unused_1', 0),
    ByteField('navRate', 1),
    ByteField('unused_3', 0),
    ByteEnumField('timeRef', 1, {0: 'UTC',
                                 1: 'GPS',
                                 2: 'GLONASS',
                                 3: 'BeiDou',
                                 4: 'Galileo'}),
    ByteField('unused_5', 0),
    XByteField('ck_a', None),
    XByteField('ck_b', None)]


def Checksum(packet):
  packet_bytes = [packet.message_class,
                  packet.message_id,
                  packet.length,
                  0,  # Length is a 2 bit field.
                  packet.measRate,
                  packet.unused_1,
                  packet.navRate,
                  packet.unused_3,
                  packet.timeRef,
                  packet.unused_5]
  ck_a, ck_b = 0, 0
  for byte in packet_bytes:
    ck_a += byte
    ck_b += ck_a
  ck_a = (ck_a % 256)
  ck_b = (ck_b % 256)
  return ck_a, ck_b

packet = UbxCfgGRate()
ck_a, ck_b = (Checksum(packet))
packet.ck_a = ck_a
packet.ck_b = ck_b
print packet.show()

with serial.Serial('/dev/ttyACM0') as gps:
  gps.write(raw(packet))
