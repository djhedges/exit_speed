from absl import app
from absl import flags
from absl import logging

from exit_speed import exit_speed_pb2
from exit_speed import sensor
from exit_speed import waveshare_lib


class Can(sensor.SensorBase):
  PROTO_CLASS = exit_speed_pb2.CAN

  def __init__(self,
             start_time: datetime.datetime,
             config: Dict,
             point_queue: multiprocessing.Queue):
    self.waveshare = waveshare_lib.WaveshareSerial()
    super().__init__(start_time, config, point_queue)

  def Loop(self):
    for can_id, data in self.waveshare.ReadFrames():
      while not self.stop_process_signal.value:
        logging.log_every_n_seconds(logging.DEBUG,
                                    'CAN ID: %s Raw Data: %s',
                                    10, can_id, data)
        proto = exit_speed_pb2.CAN()
        self.LogAndExportProto(proto)
