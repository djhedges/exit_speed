import datetime
import multiprocessing
import struct
from typing import Dict
from absl import logging

from exit_speed import exit_speed_pb2
from exit_speed import can_sensor


class Pdm(can_sensor.CanSensor):
  """Logs Link Razor PDM CAN data."""
  PROTO_CLASS = exit_speed_pb2.Pdm

  def __init__(self,
             start_time: datetime.datetime,
             config: Dict,
             point_queue: multiprocessing.Queue,
             can_data_queue: multiprocessing.Queue):
    self.pdm_proto = exit_speed_pb2.Pdm()
    super().__init__(start_time, config, point_queue, can_data_queue)

  def ParsePdmFrame(self, data: bytes) -> None:
    frame_number = data[0]
    if frame_number <= 11:  # IO Status Streams
      status = data[1]
      # Big Endian (MSB First)
      freq = (data[2] << 8) + data[3]
      # Duty cycle is signed for HP outputs (0-3), unsigned for ADIO (4-11)
      if frame_number < 4:
        duty_cycle_raw = struct.unpack('>h', data[4:6])[0]
      else:
        duty_cycle_raw = struct.unpack('>H', data[4:6])[0]
      value_raw = struct.unpack('>h', data[6:8])[0]

      if frame_number == 0:
        logging.log_every_n_seconds(logging.DEBUG, 'PDM HP1 status: %s', 10, status)
        if self.pdm_proto.hp_output_1_status:
           self.LogAndExportProto(self.pdm_proto)
           self.pdm_proto = exit_speed_pb2.Pdm()
        self.pdm_proto.hp_output_1_status = status
        self.pdm_proto.hp_output_1_freq = freq
        self.pdm_proto.hp_output_1_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.hp_output_1_current = value_raw * 0.01
      elif frame_number == 1:
        self.pdm_proto.hp_output_2_status = status
        self.pdm_proto.hp_output_2_freq = freq
        self.pdm_proto.hp_output_2_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.hp_output_2_current = value_raw * 0.01
      elif frame_number == 2:
        self.pdm_proto.hp_output_3_status = status
        self.pdm_proto.hp_output_3_freq = freq
        self.pdm_proto.hp_output_3_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.hp_output_3_current = value_raw * 0.01
      elif frame_number == 3:
        self.pdm_proto.hp_output_4_status = status
        self.pdm_proto.hp_output_4_freq = freq
        self.pdm_proto.hp_output_4_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.hp_output_4_current = value_raw * 0.01
      elif frame_number == 4:
        self.pdm_proto.adio_1_status = status
        self.pdm_proto.adio_1_freq = freq
        self.pdm_proto.adio_1_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_1_voltage = value_raw * 0.01
      elif frame_number == 5:
        self.pdm_proto.adio_2_status = status
        self.pdm_proto.adio_2_freq = freq
        self.pdm_proto.adio_2_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_2_voltage = value_raw * 0.01
      elif frame_number == 6:
        self.pdm_proto.adio_3_status = status
        self.pdm_proto.adio_3_freq = freq
        self.pdm_proto.adio_3_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_3_voltage = value_raw * 0.01
      elif frame_number == 7:
        self.pdm_proto.adio_4_status = status
        self.pdm_proto.adio_4_freq = freq
        self.pdm_proto.adio_4_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_4_voltage = value_raw * 0.01
      elif frame_number == 8:
        self.pdm_proto.adio_5_status = status
        self.pdm_proto.adio_5_freq = freq
        self.pdm_proto.adio_5_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_5_voltage = value_raw * 0.01
      elif frame_number == 9:
        self.pdm_proto.adio_6_status = status
        self.pdm_proto.adio_6_freq = freq
        self.pdm_proto.adio_6_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_6_voltage = value_raw * 0.01
      elif frame_number == 10:
        self.pdm_proto.adio_7_status = status
        self.pdm_proto.adio_7_freq = freq
        self.pdm_proto.adio_7_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_7_voltage = value_raw * 0.01
      elif frame_number == 11:
        self.pdm_proto.adio_8_status = status
        self.pdm_proto.adio_8_freq = freq
        self.pdm_proto.adio_8_duty_cycle = duty_cycle_raw * 0.01
        self.pdm_proto.adio_8_voltage = value_raw * 0.01
    elif frame_number == 50:  # Health
      # Temperature is +50 offset. 
      # Celsius to Fahrenheit: (C * 9/5) + 32
      pdm_temp_c = data[1] - 50
      self.pdm_proto.pdm_temp_f = (pdm_temp_c * 9/5) + 32
      self.pdm_proto.pdm_voltage = data[2] * 0.1

  def Loop(self) -> None:
    while not self.stop_process_signal.value:
      _, data = self.can_data_queue.get()
      logging.log_every_n_seconds(logging.DEBUG, 'PDM Data: %s', 10, data)
      self.ParsePdmFrame(data)
