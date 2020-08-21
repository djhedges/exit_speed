#!/usr/bin/python3

import logging
import os
import gps_pb2


def ReadLog(log_path):
  """Reads old data log format."""
  session = gps_pb2.Session()
  with open(log_path, 'rb') as log_file:
    session.ParseFromString(log_file.read())
  return session
