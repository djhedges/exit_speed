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
  channel = grpc.insecure_channel('./.reflector_socket')
  stub = reflector_pb2_grpc.ReflectStub(channel)
  lap_number = reflector_pb2.LapNumber()
  lap_number.lap_number = 7
  stub.NewLap(lap_number)


if __name__ == '__main__':
  app.run(main)
