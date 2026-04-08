import datetime
import multiprocessing
from typing import Dict
from absl import logging

from exit_speed import exit_speed_pb2
from exit_speed import can_sensor


class Egts(can_sensor.CanSensor):
  """Logs EGTs CAN data."""
  PROTO_CLASS = exit_speed_pb2.Egts

  def __init__(self,
             start_time: datetime.datetime,
             config: Dict,
             point_queue: multiprocessing.Queue,
             can_data_queue: multiprocessing.Queue):
    self.egts_proto = exit_speed_pb2.Egts()
    super().__init__(start_time, config, point_queue, can_data_queue)

  def ParseEgtsFrame(self, can_id: int, data: bytes) -> None:
    if can_id == 1797:
      if self.egts_proto.egt_1_f and self.egts_proto.egt_6_f:
        self.LogAndExportProto(self.egts_proto)
        self.egts_proto = exit_speed_pb2.Egts()
      self.egts_proto.egt_1_f = ((data[0] << 8) + data[1]) / 4.0 * 9 / 5 + 32
      self.egts_proto.egt_2_f = ((data[2] << 8) + data[3]) / 4.0 * 9 / 5 + 32
      self.egts_proto.egt_3_f = ((data[4] << 8) + data[5]) / 4.0 * 9 / 5 + 32
      self.egts_proto.egt_4_f = ((data[6] << 8) + data[7]) / 4.0 * 9 / 5 + 32
    elif can_id == 1798:
      self.egts_proto.egt_5_f = ((data[0] << 8) + data[1]) / 4.0 * 9 / 5 + 32
      self.egts_proto.egt_6_f = ((data[2] << 8) + data[3]) / 4.0 * 9 / 5 + 32

  def Loop(self) -> None:
    while not self.stop_process_signal.value:
      can_id, data = self.can_data_queue.get()
      self.ParseEgtsFrame(can_id, data)
