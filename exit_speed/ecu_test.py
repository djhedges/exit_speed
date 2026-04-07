"""Unitests for ecu.py"""
import datetime
import multiprocessing
import unittest
from unittest import mock
from absl.testing import absltest
from exit_speed import ecu
from exit_speed import exit_speed_pb2
from exit_speed import postgres_test_lib

class TestEcu(postgres_test_lib.PostgresTestBase, unittest.TestCase):
  """Ecu unittests."""

  def setUp(self):
    super().setUp()
    self.start_time = datetime.datetime.now()
    self.config = {'car': 'corrado'}
    self.point_queue = multiprocessing.Queue()
    self.can_data_queue = multiprocessing.Queue()
    self.ecu = ecu.Ecu(self.start_time, self.config,
                       self.point_queue, self.can_data_queue)

  def testParseLinkDashFrame(self):
    frames = [
      [0, 0, 0, 0, 0, 0, 0, 0],
      [1, 0, 233, 3, 0, 0, 0, 0],
      [2, 0, 0, 0, 0, 0, 91, 0],
      [3, 0, 50, 0, 20, 5, 0, 0],
      [4, 0, 0, 0, 0, 0, 232, 3],
      [5, 0, 0, 0, 0, 0, 0, 0],
      [6, 0, 0, 0, 0, 0, 0, 0],
      [8, 0, 69, 0, 1, 0, 0, 0],
      [9, 0, 0, 0, 0, 0, 0, 0],
      [10, 0, 0, 0, 0, 0, 0, 0],
      [11, 0, 0, 0, 0, 0, 0, 0],
      [12, 0, 0, 0, 0, 0, 0, 0],
      [13, 0, 0, 0, 0, 0, 0, 0],
    ]
    for frame in frames:
      self.ecu.ParseLinkDashFrame(frame)


if __name__ == '__main__':
  absltest.main()
