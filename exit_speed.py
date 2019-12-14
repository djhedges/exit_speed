#! /usr/bin/python

import gps_pb2 
from gps import *
    
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 
   
try:
  while True:
    report = gpsd.next() #
    # Mode 1 == no fix, 2 == 2D fix and 3 == 3D fix.
    if report['class'] == 'TPV' and report.mode == 3:
      point = gps_pb2.Point()
      point.lat = report.lat
      point.lon = report.lon
      point.alt = report.alt
      point.speed = report.speed
      point.time.FromJsonString(report.time)
      print point
 
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
  print "Done.\nExiting."
  gpsd.close()
