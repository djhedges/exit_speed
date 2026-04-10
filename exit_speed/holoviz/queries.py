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
"""Dashboard queries."""
import textwrap
from typing import List
from typing import Text
import pandas as pd
from exit_speed import postgres
from exit_speed import tracks


def GetTracks() -> List[Text]:
  return [track.name for track in tracks.TRACK_LIST]


def GetSessions() -> pd.DataFrame:
  select_statement = textwrap.dedent("""
  SELECT
    TO_CHAR((duration_ns / 1e6 || 'millisecond')::interval, 'MI:SS:MS') AS lap_time,
    TO_CHAR(sessions.time AT TIME ZONE 'PDT', 'YYYY-MM-DD HH:MI:SS') as session_time,
    laps.number AS lap_number,
    track
  FROM laps
  JOIN sessions ON laps.session_id = sessions.id
  WHERE
    duration_ns IS NOT NULL
  ORDER BY lap_time ASC
  """)
  with postgres.ConnectToDB() as conn:
    return pd.io.sql.read_sql(select_statement, conn)
