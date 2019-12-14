#!/usr/bin/python

import sys
import log_files

session = log_files.ReadLog(sys.argv[1])
for lap in session.laps:
  for point in lap.points:
    print point
