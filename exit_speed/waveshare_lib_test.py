"""Unitests for waveshare_lib.py"""
import unittest
import mock
import serial
from absl.testing import absltest
from exit_speed import waveshare_lib


class TestWaveshareLib(unittest.TestCase):
  """Waveshare Serial unittests."""

  def testCalculateChecksum(self):
    data = [0xaa, 0x55, 0x12, 0x03, 0x01]
    self.assertEqual(0x16, waveshare_lib.calculate_checksum(data))

  @mock.patch('serial.Serial')
  def testSetBaudRate(self, mock_serial):
    instance = mock_serial.return_value
    waveshare = waveshare_lib.WaveshareSerial(start_process=False)
    waveshare.SetBaudRate()
    expected = bytes([
        0xaa, 0x55, 0x12, 0x03, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16])
    instance.write.assert_called_with(expected)

  @mock.patch('serial.Serial')
  def testReadFramesStandard(self, mock_serial):
    instance = mock_serial.return_value
    instance.read.side_effect = [
        b'\xaa\xc2', b'\x23\x01\xde\xad\x55'
    ]
    waveshare = waveshare_lib.WaveshareSerial(start_process=False)
    frames = waveshare.ReadFrames()
    can_id, data = next(frames)
    self.assertEqual(0x123, can_id)
    self.assertEqual([0xde, 0xad], data)

if __name__ == '__main__':
  absltest.main()
