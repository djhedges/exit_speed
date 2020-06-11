#!/usr/bin/python3

import logging
import os
import gps_pb2

LAP_LOGS = '/home/pi/lap_logs'

def SaveSessionToDisk(session):
  if not os.path.exists(LAP_LOGS):
    os.mkdir(LAP_LOGS)
  first_lap = session.laps[0].points[0]
  filename = 'data-%s' % first_lap.time.ToJsonString()
  logging.info(f'Saving session data to {filename}')
  with open(os.path.join(LAP_LOGS, filename), 'wb') as log_file:
    log_file.write(session.SerializeToString())


def ReadLog(log_path):
  session = gps_pb2.Session()
  with open(log_path, 'rb') as log_file:
    session.ParseFromString(log_file.read())
  return session
