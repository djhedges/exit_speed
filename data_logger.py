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

from absl import logging
from typing import Generator
from google.protobuf import message
import gps_pb2

PROTO_LEN_BYTES = 2
BYTE_ORDER = 'big'


class Logger(object):

  def __init__(self, file_path):
    self.file_path = file_path
    self.current_file = None

  def _GetFile(self):
    if not self.current_file:
      self.current_file = open(self.file_path, 'wb')
    return self.current_file

  def WriteProto(self, proto: gps_pb2.Point):
    proto_bytes = proto.SerializePartialToString()
    proto_len = len(proto_bytes)
    data_file = self._GetFile()
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
          except:
            logging.info('Decode error.  Likely the file writes were '
                         'interrupted.  Treating as end of file.')
            break
        else:
          break
