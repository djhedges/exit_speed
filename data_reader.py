#!/usr/bin/python3
"""Library for reading a exit speed data file."""

import gps_pb2
import tensorflow as tf
# Needed in order to iterate over the files.
tf.compat.v1.enable_eager_execution()


def ReadData(filepath):
  """Returns a list of gps_pb.Point protobufs."""
  points = []
  data = tf.data.TFRecordDataset(filepath)
  for record in data:
    point = gps_pb2.Point()
    point.ParseFromString(record.numpy())
    points.append(point)
  return points
