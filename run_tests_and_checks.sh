#!/bin/bash
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
set -e
set -x
CODE_PATH="$(dirname $0)"
for test_file in $(ls "${CODE_PATH}"/*_test.py); do
  if [ $test_file != "./replay_data_test.py" ]; then
    echo bash -c $test_file
  fi
done
pytype *.py
pylint --ignore-patterns=gps_pb2.py *.py
