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
"""Client library for the reflector.
"""

from absl import app
import grpc
import reflector_pb2
import reflector_pb2_grpc


def main(unused_argv):
  channel = grpc.insecure_channel('unix:///tmp/exit_speed.sock')
  stub = reflector_pb2_grpc.ReflectStub(channel)
  point_update = reflector_pb2.PointUpdate()
  point_update.lap_number = 1
  response = stub.ExportPoint(point_update)
  import pdb; pdb.set_trace()


if __name__ == '__main__':
  app.run(main)
