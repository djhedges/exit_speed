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
import hvplot.pandas
import pandas as pd
from absl import app
from exit_speed.holoviz import queries
from exit_speed.tracks import portland_internal_raceways

def make_dashboard():
  sessions = queries.GetSessions()
  tracks = queries.GetTracks()
  metrics = sorted(list(queries.GetPointsColumns()))
  if 'speed_ms' in metrics:
    metrics.remove('speed_ms')
    metrics.append('speed_mph')
  metrics = sorted(metrics)

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

  metrics_selection = pn.widgets.MultiChoice(
      name='Metrics', 
      options=metrics, 
      value=['speed_mph'])

  @pn.depends(track_dropdown, watch=True)
  def _update_table(track):
    sessions_table.value = sessions[sessions.track == track]

  @pn.depends(sessions_table.param.selection, metrics_selection)
  def make_plots(selection, selected_metrics):
    if not selection or not selected_metrics:
      return pn.pane.Markdown("### Select laps and metrics to display plots")
    
    selected_df = sessions_table.value.iloc[selection]
    all_laps_data = []
    
    columns_to_fetch = set(selected_metrics)
    if 'speed_mph' in columns_to_fetch:
      columns_to_fetch.remove('speed_mph')
      columns_to_fetch.add('speed_ms')
    columns_to_fetch.add('elapsed_distance_m')

    for _, row in selected_df.iterrows():
      start_time, end_time = queries.GetLapTableData(row['session_id'], row['lap_number'])
      lap_data = queries.GetLapData(columns_to_fetch, start_time, end_time)
      if lap_data is not None:
        if 'speed_ms' in lap_data.columns:
          lap_data['speed_mph'] = lap_data['speed_ms'] * 2.236936
        lap_data['lap_number'] = row['lap_number']
        lap_data['session_id'] = row['session_id']
        lap_data['legend_label'] = f"Lap {row['lap_number']} (Session {row['session_id']})"
        all_laps_data.append(lap_data)
    
    if not all_laps_data:
      return pn.pane.Markdown("### No data found for selected laps")
    
    df = pd.concat(all_laps_data)
    
    plots = []
    for metric in selected_metrics:
      if metric in df.columns:
        plot = df.hvplot.line(
            x='elapsed_distance_m', 
            y=metric, 
            by='legend_label', 
            title=f"{metric} vs Distance",
            height=300,
            width=800)
        plots.append(plot)
    
    return pn.Column(*plots)

  title = pn.pane.Markdown("# Exit Speed HoloViz Dashboard")
  return pn.Column(
      title, 
      track_dropdown, 
      sessions_table, 
      metrics_selection,
      make_plots)


def main(unused_argv):
  pn.extension('tabulator')
  pn.serve(make_dashboard, port=5006, show=False)


if __name__ == '__main__':
  app.run(main)
