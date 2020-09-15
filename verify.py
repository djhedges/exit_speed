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
"""Quick verification of the new data."""

import os
import data_reader
import data_logger

LOG_DIR = '/home/pi/lap_logs_with_tensorflow/'
for file_name in os.listdir(LOG_DIR):
  if file_name.endswith('tfr'):
    points = None
    full_path = os.path.join(LOG_DIR, file_name)
    prefix = full_path[:-4]
    print('%s | %s' % (full_path, prefix))
    try:
      points = data_reader.ReadData(full_path)
    except Exception:
      print('tensorflow could not read file')
    if points:
      logger = data_logger.Logger(prefix)
      new = [point for point in logger.ReadProtos()]
      if points != new:
        import pdb; pdb.set_trace()
