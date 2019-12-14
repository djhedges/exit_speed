#!/usr/bin/python

import os
import log_files
import gps_pb2 
from gps import *
    
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 


def RecordLap():
  split = 10 * 60 # Every 60 seconds.
  counter = 0 
  session = gps_pb2.Session()
  lap = session.laps.add()
  while counter < split:
    counter += 1
    report = gpsd.next() #
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      point = lap.points.add()
      point.lat = report.lat
      point.lon = report.lon
      point.alt = report.alt
      point.speed = report.speed
      point.time.FromJsonString(report.time)
  print lap
  log_files.SaveSessionToDisk(session)

   
try:
  while True:
    RecordLap()

 
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
  print "Done.\nExiting."
  gpsd.close()
