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
"""Portland International Raceway."""
from exit_speed.tracks import base

PortlandInternationalRaceway = base.Track(
    name='Portland International Raceway',
    start_finish=(45.595015, -122.694526),
    turns=(
        #base.Turn('1', 45.596143, -122.698153),
        #base.Turn('2', 45.596494, -122.698325),
        #base.Turn('3', 45.596531, -122.699786),
        base.Turn('4', 45.597368, -122.702836),
        base.Turn('4a', 45.598057, -122.703058),
        base.Turn('5', 45.598724, -122.701839),
        base.Turn('6', 45.597977, -122.700049),
        base.Turn('7', 45.599913, -122.699313),
        base.Turn('8', 45.599559, -122.697438),
        base.Turn('9', 45.599445, -122.696173),
        base.Turn('10', 45.595370, -122.689487),
        base.Turn('11', 45.595004, -122.688507),
        base.Turn('12', 45.593828, -122.687975),
        ))
