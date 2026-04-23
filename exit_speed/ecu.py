import datetime
import multiprocessing
import struct
from typing import Dict
from absl import logging

from exit_speed import exit_speed_pb2
from exit_speed import can_sensor


class Ecu(can_sensor.CanSensor):
  """Logs Link ECU Fury Generic Dash stream CAN data."""
  PROTO_CLASS = exit_speed_pb2.Ecu

  def __init__(self,
             start_time: datetime.datetime,
             config: Dict,
             point_queue: multiprocessing.Queue,
             can_data_queue: multiprocessing.Queue):
    self.ecu_proto = exit_speed_pb2.Ecu()
    super().__init__(start_time, config, point_queue, can_data_queue)

  def ParseLinkDashFrame(self, data: bytes) -> None:
     index, _, raw1, raw2, raw3 = struct.unpack('<BBHHH', data)
     logging.log_every_n_seconds(logging.DEBUG, 'ECU Frame Index: %s', 10, index)
     if index == 0:
       if self.ecu_proto.map_psi > 0:  # Export a full proto.
        self.LogAndExportProto(self.ecu_proto)
        self.ecu_proto = exit_speed_pb2.Ecu()
       self.ecu_proto.rpm = raw1
       self.ecu_proto.map_psi = raw2 * 0.1450377377
       self.ecu_proto.mgp_psi = (raw3 - 100) * 0.1450377377

     elif index == 1:
       self.ecu_proto.barometric_pressure_psi = raw1 * 0.1 * 0.1450377377
       self.ecu_proto.tps = raw2 * 0.1
       self.ecu_proto.injector_dc = raw3 * 0.1

     elif index == 2:
       self.ecu_proto.injector_dc_sec = raw1 * 0.1
       self.ecu_proto.injector_pulse_width = raw2 * 0.001
       self.ecu_proto.ect_f = (raw3 - 50) * 9 / 5 + 32

     elif index == 3:
       self.ecu_proto.iat_f = (raw1 - 50) * 9 / 5 + 32
       self.ecu_proto.ecu_volts = raw2 * 0.01
       self.ecu_proto.maf = raw3 * 0.1

     elif index == 4:
       self.ecu_proto.gear_position = raw1
       self.ecu_proto.injector_timing = raw2
       self.ecu_proto.ignition_timing = (raw3 * 0.1) - 100

     elif index == 6:
       self.ecu_proto.lambda_1 = raw2 * 0.001

     elif index == 7:
       self.ecu_proto.trig_1_error_counter = raw1
       self.ecu_proto.fault_codes = raw2
       self.ecu_proto.fuel_pressure_psi = raw3 * 0.1450377377

     elif index == 8:
       self.ecu_proto.oil_temp_f = (raw1 - 50) * 9 / 5 + 32
       self.ecu_proto.oil_pressure_psi = raw2 * 0.1450377377

     elif index == 10:
       self.ecu_proto.knock_level_1 = raw1 * 5
       self.ecu_proto.knock_level_2 = raw2 * 5

  def ParseBrakePressure(self, data: bytes) -> None:
    front_mv = int.from_bytes(data[0:2], 'big')
    rear_mv = int.from_bytes(data[2:4], 'big')
    # (mV / 1000 - 0.5) * 500 = PSI
    # Link ECU Useer stream is multipling by 1000 to move the decimal.
    self.ecu_proto.front_brake_pressure_psi = (front_mv / 1000.0 - 0.5) * 500.0
    self.ecu_proto.rear_brake_pressure_psi = (rear_mv / 1000.0 - 0.5) * 500.0

  def Loop(self) -> None:
    while not self.stop_process_signal.value:
      can_id, data = self.can_data_queue.get()
      logging.log_every_n_seconds(logging.DEBUG,
                                  'ECU Data: %s',
                                  10, data)
      if can_id == 56:
        self.ParseLinkDashFrame(data)
      elif can_id == 182:
        self.ParseBrakePressure(data)
