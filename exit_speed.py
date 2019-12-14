#!/usr/bin/python

import os
import gps_pb2 
from gps import *
    
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 

LAP_LOGS = '/home/pi/lap_logs'


def SaveLapToDisk(lap):
  if not os.path.exists(LAP_LOGS):
    os.mkdir(LAP_LOGS)
  first_lap = lap.points[0]
  with open(os.path.join(LAP_LOGS, 
            first_lap.time.ToJsonString()), 'w') as lap_file:
    lap_file.write(lap.SerializeToString())

   
lap = gps_pb2.Lap()
try:
  while True:
    report = gpsd.next() #
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      point = lap.points.add()
      point.lat = report.lat
      point.lon = report.lon
      point.alt = report.alt
      point.speed = report.speed
      point.time.FromJsonString(report.time)

 
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
  print "Done.\nExiting."
  SaveLapToDisk(lap)
  gpsd.close()
