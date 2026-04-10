#!/usr/bin/python3
# Copyright 2026 Douglas Hedges
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
"""HoloViz dashboard for Exit Speed."""

import panel as pn
from absl import app
from exit_speed.holoviz import queries
from exit_speed.tracks import portland_internal_raceways

def main(unused_argv):
  pn.extension()
  
  sessions = queries.GetSessions()
  tracks = queries.GetTracks()

  track_dropdown = pn.widgets.Select(
      name='Track', 
      options=tracks, 
      value=portland_internal_raceways.PortlandInternationalRaceway.name)

  @pn.depends(track_dropdown.param.value)
  def get_sessions_df(track):
    df = sessions[sessions.track == track]
    return df

  sessions_table = pn.widgets.DataFrame(get_sessions_df, width=800)
  
  title = pn.pane.Markdown("# Exit Speed HoloViz Dashboard")
  dashboard = pn.Column(title, track_dropdown, sessions_table)
  
  # Serve the dashboard
  pn.serve(dashboard, port=5006, show=False)


if __name__ == '__main__':
  app.run(main)
