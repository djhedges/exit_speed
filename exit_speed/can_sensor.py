"""Library for CAN based sensors."""
import datetime
import multiprocessing
from typing import Dict
from exit_speed import sensor


class CanSensor(sensor.SensorBase):

  def __init__(self,
             start_time: datetime.datetime,
             config: Dict,
             point_queue: multiprocessing.Queue,
             can_data_queue: multiprocessing.Queue):
    self.can_data_queue = can_data_queue
    super().__init__(start_time, config, point_queue)
