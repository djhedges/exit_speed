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
  pn.extension('tabulator')
  
  sessions = queries.GetSessions()
  tracks = queries.GetTracks()

  track_dropdown = pn.widgets.Select(
      name='Track', 
      options=tracks, 
      value=portland_internal_raceways.PortlandInternationalRaceway.name)

  sessions_table = pn.widgets.Tabulator(
      sessions[sessions.track == track_dropdown.value], 
      width=800, 
      selectable='checkbox',
      pagination='remote',
      page_size=10)

  @pn.depends(track_dropdown, watch=True)
  def _update_table(track):
    sessions_table.value = sessions[sessions.track == track]

  @pn.depends(sessions_table.param.selection)
  def selected_laps_display(selection):
    if not selection:
      return "### Selected Laps: None"
    selected_df = sessions_table.value.iloc[selection]
    return f"### Selected Laps: {selected_df['lap_number'].tolist()}"

  title = pn.pane.Markdown("# Exit Speed HoloViz Dashboard")
  dashboard = pn.Column(
      title, 
      track_dropdown, 
      sessions_table, 
      selected_laps_display)
  
  # Serve the dashboard
  pn.serve(dashboard, port=5006, show=False)


if __name__ == '__main__':
  app.run(main)
