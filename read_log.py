#!/usr/bin/python

import os
import sys
import gps_pb2 
from gps import *
    
LAP_LOGS = '/home/pi/lap_logs'

def ReadLog():
  with open(sys.argv[1]) as lap_log:
    lap = gps_pb2.Lap()
    lap.ParseFromString(lap_log.read())
    for point in lap.points:
      print point

ReadLog()
