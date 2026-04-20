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
import holoviews as hv
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
    if 'gsum' in columns_to_fetch:
      columns_to_fetch.remove('gsum')
      columns_to_fetch.update(['accelerometer_x', 'accelerometer_y'])
    columns_to_fetch.add('elapsed_distance_m')

    for _, row in selected_df.iterrows():
      start_time, end_time = queries.GetLapTableData(row['session_id'], row['lap_number'])
      lap_data = queries.GetLapData(columns_to_fetch, start_time, end_time)
      if lap_data is not None:
        if 'speed_ms' in lap_data.columns:
          lap_data['speed_mph'] = lap_data['speed_ms'] * 2.236936
        if 'accelerometer_x' in lap_data.columns and 'accelerometer_y' in lap_data.columns:
          lap_data['gsum'] = lap_data['accelerometer_x'].abs() + lap_data['accelerometer_y'].abs()
        lap_data['lap_number'] = row['lap_number']
        lap_data['session_id'] = row['session_id']
        lap_data['legend_label'] = f"Lap {row['lap_number']} (Session {row['session_id']})"
        all_laps_data.append(lap_data)
    
    if not all_laps_data:
      return pn.pane.Markdown("### No data found for selected laps")
    
    df = pd.concat(all_laps_data)

    pointer = hv.streams.PointerX(x=0)
    vline = hv.DynamicMap(lambda x: hv.VLine(x or 0), streams=[pointer]).opts(
        line_width=0.5, line_color='lightgrey')

    def get_hover_text(x, metric_name):
      if x is None:
        return hv.Text(0, 0, "")
      # Find the closest value in the data for each lap
      laps_at_x = []
      for label in df.legend_label.unique():
        lap_df = df[df.legend_label == label]
        subset = lap_df[lap_df.elapsed_distance_m >= x].head(1)
        if subset.empty:
          subset = lap_df.tail(1)
        val = subset[metric_name].values[0]
        laps_at_x.append(f"{label}: {val:.2f}")
      
      text = "\n".join(laps_at_x)
      # Position text at the top of the plot to avoid overlapping lines
      y_max = df[metric_name].max()
      return hv.Text(x, y_max, text, halign='left', valign='top', fontsize=8)

    plots = []
    for metric in selected_metrics:
      if metric in df.columns:
        plot = df.hvplot.line(
            x='elapsed_distance_m', 
            y=metric, 
            by='legend_label', 
            title=f"{metric} vs Distance",
            height=300,
            responsive=True)
        # Add shared_axes=True to ensure syncing
        text_annotation = hv.DynamicMap(lambda x, m=metric: get_hover_text(x, m), streams=[pointer])
        plots.append((plot * vline * text_annotation).opts(shared_axes=True))

    return pn.GridBox(*plots, ncols=2, sizing_mode='stretch_width')

  title = pn.pane.Markdown("# Exit Speed HoloViz Dashboard", sizing_mode='stretch_width')
  return pn.Column(
      title, 
      track_dropdown, 
      sessions_table, 
      metrics_selection,
      make_plots,
      sizing_mode='stretch_width')


def main(unused_argv):
  pn.extension('tabulator')
  pn.serve(make_dashboard, port=5006, show=False)


if __name__ == '__main__':
  app.run(main)
