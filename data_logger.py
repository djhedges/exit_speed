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
"""Library for appending protos to a file.

Based the recommendation here.
https://developers.google.com/protocol-buffers/docs/techniques
"""

import os
from absl import logging
from typing import Generator
from typing import Text
from google.protobuf import message
import gps_pb2

PROTO_LEN_BYTES = 1
BYTE_ORDER = 'big'


class Logger(object):
  """Interface for writing and reading protos to disk."""

  def __init__(self, file_prefix_or_name: Text):
    """Initializer.

    Args:
      file_prefix: File prefix with out the .data extension.
                   Ex: testdata/PIR_race_10hz_gps_only_2020-06-21
                   Or the a file's complete name including the _#.data suffix.
    """
    super().__init__()
    if file_prefix_or_name.endswith('.data'):
      self.file_prefix = file_prefix_or_name[:-7]  # Chop off the _1.data
    else:
      self.file_prefix = file_prefix_or_name
    self.file_path = None
    self.current_file = None
    self.current_proto_len = PROTO_LEN_BYTES
    self._SetFilePath()

  def __del__(self):
    if self.current_file:
      self.current_file.close()

  def _SetFilePath(self):
    self.file_path = '%s_%s.data' % (self.file_prefix, self.current_proto_len)

  def _SetCurrentFile(self):
    if self.current_file:
      self.current_file.flush()
    parent_dir = os.path.dirname(self.file_path)
    if not os.path.exists(parent_dir):
      os.mkdir(parent_dir)
    self.current_file = open(self.file_path, 'wb')

  def GetFile(self, proto_len):
    if proto_len < int.from_bytes(b'\xff' * self.current_proto_len, 'big'):
      if not self.current_file:
        self._SetCurrentFile()
    else:
      self.current_proto_len += 1
      self._SetFilePath()
      self._SetCurrentFile()
    return self.current_file

  def WriteProto(self, proto: gps_pb2.Point):
    proto_bytes = proto.SerializePartialToString()
    proto_len = len(proto_bytes)
    data_file = self.GetFile(proto_len)
    data_file.write(proto_len.to_bytes(
      PROTO_LEN_BYTES, BYTE_ORDER) + proto_bytes)

  def ReadProtos(self) -> Generator[gps_pb2.Point, None, None]:
    with open(self.file_path, 'rb') as data_file:
      while True:
        proto_len = int.from_bytes(data_file.read(PROTO_LEN_BYTES), BYTE_ORDER)
        proto_bytes = data_file.read(proto_len)
        if proto_len and proto_bytes:
          try:
            point = gps_pb2.Point.FromString(proto_bytes)
            yield point
          except message.DecodeError:
            logging.info('Decode error.  Likely the file writes were '
                         'interrupted.  Treating as end of file.')
            break
        else:
          break
