#!/usr/bin/python3
# Copyright 2021 Google LLC
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
"""Backups ~/lap_logs to GCS without writing to SD.

GOOGLE_APPLICATION_CREDENTIALS=<service>.json ./gcs_archive.py
"""
import datetime
import io
import tarfile

from absl import app
from absl import flags
from google.cloud import storage

FLAGS = flags.FLAGS
flags.DEFINE_string('data_log_path', '/home/pi/lap_logs',
                    'The directory containing lap logs.')
flags.DEFINE_string('gcs_bucket_name', 'lap_logs',
                    'The directory containing lap logs.')


def main(unused_argv):
  mem_file = io.BytesIO()
  with tarfile.open(fileobj=mem_file, mode='w:bz2') as tar:
    tar.add(FLAGS.data_log_path)
  mem_file.seek(0)
  storage_client = storage.Client()
  bucket = storage_client.bucket(FLAGS.gcs_bucket_name)
  today = datetime.date.today()
  blob_name = 'lap_logs_%s.tar.bz2' % today.strftime('%Y%m%d')
  blob = bucket.blob(blob_name)
  blob.upload_from_file(mem_file)


if __name__ == '__main__':
  app.run(main)
