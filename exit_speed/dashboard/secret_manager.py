# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Library for requesting secrets."""
import json


def GetSecret(secret_id):
  # This module is difficult to get working on a Pi so let's load it only on
  # App Engine for now.
  # pylint: disable=import-outside-toplevel
  from google.cloud import secretmanager
  client = secretmanager.SecretManagerServiceClient()
  response = client.access_secret_version(request={'name': secret_id})
  return json.loads(response.payload.data)
