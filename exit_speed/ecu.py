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
     index, _, raw1, raw2, raw3 = struct.unpack('<BBHHH', bytes(data))
     if index == 0:
       if self.ecu_proto.map > 0:  # Export a full proto.
        self.LogAndExportProto(self.ecu_proto)
        self.ecu_proto = exit_speed_pb2.Ecu()
       self.ecu_proto.rpm = raw1
       self.ecu_proto.map = raw2
       self.ecu_proto.mgp = raw3 - 100

     elif index == 1:
       self.ecu_proto.barometric_pressure = raw1 * 0.1
       self.ecu_proto.tps = raw2 * 0.1
       self.ecu_proto.injector_dc = raw3 * 0.1

     elif index == 2:
       self.ecu_proto.injector_dc_sec = raw1 * 0.1
       self.ecu_proto.injector_pulse_width = raw2 * 0.001
       self.ecu_proto.ect = raw3 - 50

     elif index == 3:
       self.ecu_proto.iat = raw1 - 50
       self.ecu_proto.ecu_volts = raw2 * 0.01
       self.ecu_proto.maf = raw3 * 0.1

     elif index == 4:
       self.ecu_proto.gear_position = raw1
       self.ecu_proto.injector_timing = raw2
       self.ecu_proto.ignition_timing = (raw3 * 0.1) - 100

     elif index == 5:
       self.ecu_proto.cam_inlet_bank_1 = raw1 * 0.1
       self.ecu_proto.cam_inlet_bank_2 = raw2 * 0.1
       self.ecu_proto.cam_exhaust_bank_1 = raw3 * -0.1

     elif index == 6:
       self.ecu_proto.cam_exhaust_bank_2 = raw1 * -0.1
       self.ecu_proto.lambda_1 = raw2 * 0.001
       self.ecu_proto.lambda_2 = raw3 * 0.001

     elif index == 7:
       self.ecu_proto.trig_1_error_counter = raw1
       self.ecu_proto.fault_codes = raw2
       self.ecu_proto.fuel_pressure = raw3

     elif index == 8:
       self.ecu_proto.oil_temp = raw1 - 50
       self.ecu_proto.oil_pressure = raw2
       self.ecu_proto.lf_wheel_speed = raw3 * 0.1

     elif index == 9:
       self.ecu_proto.lr_wheel_speed = raw1 * 0.1
       self.ecu_proto.rf_wheel_speed = raw2 * 0.1
       self.ecu_proto.rr_wheel_speed = raw3 * 0.1

     elif index == 10:
       self.ecu_proto.knock_level_1 = raw1 * 5
       self.ecu_proto.knock_level_2 = raw2 * 5
       self.ecu_proto.knock_level_3 = raw3 * 5

     elif index == 11:
       self.ecu_proto.knock_level_4 = raw1 * 5
       self.ecu_proto.knock_level_5 = raw2 * 5
       self.ecu_proto.knock_level_6 = raw3 * 5

     elif index == 12:
       self.ecu_proto.knock_level_7 = raw1 * 5
       self.ecu_proto.knock_level_8 = raw2 * 5
       self.ecu_proto.limits_flags = raw3

     elif index == 13:
       self.ecu_proto.aps_main = raw1 * 0.1
       self.ecu_proto.percent_ethanol = raw2
       self.ecu_proto.status_bit_field = raw3

  def Loop(self) -> None:
    while not self.stop_process_signal.value:
      data = self.can_data_queue.get()
      logging.log_every_n_seconds(logging.DEBUG,
                                  'Ecu Data: %s',
                                  10, data)
      self.ParseLinkDashFrame(data)
