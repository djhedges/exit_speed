#!/usr/bin/python3
"""Converts old data format to TFRecord."""

import sys
import log_files
import tensorflow as tf


if __name__ == '__main__':
  assert len(sys.argv) == 2
  file_path = sys.argv[1]
  session = log_files.ReadLog(file_path)
  new_path = '%s.tfr' % file_path
  print('%s > %s' % (file_path, new_path))
  with tf.io.TFRecordWriter(new_path) as writer:
    for lap in session.laps:
      for point in lap.points:
        writer.write(point.SerializeToString())
