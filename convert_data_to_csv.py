#!/usr/bin/python3

import logging
import sys
import csv_lib
import replay_data

if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  assert len(sys.argv) == 2
  file_path = sys.argv[1]
  es = replay_data.ReplayLog(file_path)
  session = es.GetSession()
  new_path = '%s_test.csv' % file_path
  print('%s > %s' % (file_path, new_path))
  csv_lib.ConvertProtoToTraqmate(session, new_path)
