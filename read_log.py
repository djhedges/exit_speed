#!/usr/bin/python3

import sys
import log_files

for arg in sys.argv[1:]:
  print(arg)
  session = log_files.ReadLog(arg)
  lap_num = 1
  for lap in session.laps:
    print(f'Lap: {lap_num}')
    lap_num += 1
    for point in lap.points:
      print(point)
