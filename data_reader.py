#!/usr/bin/python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
