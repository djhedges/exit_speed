#!/usr/bin/python

import sys
import log_files

for arg in sys.argv[1:]:
  print arg
  session = log_files.ReadLog(arg)
  for lap in session.laps:
    for point in lap.points:
      print point
