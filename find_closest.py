#!/usr/bin/python3

import attr
import log_files
import exit_speed
import statistics
import time
import numpy as np
from scipy.spatial import cKDTree

BRUTE = []
TIMING = []


def Time(timing_list):
  def decorator(func):
    def timed(*args, **kwargs):
      start = time.time()
      result = func(*args, **kwargs)
      run_time = time.time() - start
      timing_list.append(run_time)
      return result
    return timed
  return decorator


def LoadSession():
  """Testdata.

  Lap: 1, num of points: 5853
  Lap: 2, num of points: 3844
  Lap: 3, num of points: 3730
  Lap: 4, num of points: 3658
  Lap: 5, num of points: 3620
  Lap: 6, num of points: 3634
  Lap: 7, num of points: 3658
  Lap: 8, num of points: 3657
  Lap: 9, num of points: 3656
  Lap: 10, num of points: 3662
  Lap: 11, num of points: 3656
  Lap: 12, num of points: 3672
  Lap: 13, num of points: 3672
  Lap: 14, num of points: 3709
  Lap: 15, num of points: 3690
  Lap: 16, num of points: 3689
  Lap: 17, num of points: 3687
  Lap: 18, num of points: 3674
  Lap: 19, num of points: 3696
  Lap: 20, num of points: 5392
  """
  return log_files.ReadLog('testdata/data-2019-08-18T16:53:01.250Z')




@Time(BRUTE)
def BruteFindNearestPoint(point, best_points):
  """Suprisingly not terriable despite O(n^2).

  min - 0.03502225875854492
  max - 0.08478713035583496
  median - 0.03641939163208008
  total run time - 50m52.829s
  """
  nearest_delta = None
  nearest_point = None
  all_deltas = []
  for b_point in best_points:
    delta = exit_speed.PointDelta(point, b_point)
    all_deltas.append(delta)
    if not nearest_delta or delta < nearest_delta:
      nearest_delta = delta
      nearest_point = b_point
  return nearest_point


@Time(TIMING)
def KDTreeSearch(point, best_points, tree):
  neighbors = tree.query_ball_point([point.lon, point.lat], 0.0004, n_jobs=-1)
  brute_points = []
  print(len(neighbors))
  for neighbor in neighbors:
    x = tree.data[:, 0][neighbor]
    y = tree.data[:, 1][neighbor]
    for point_b in best_points:
      if point_b.lon == x and point_b.lat == y:
        brute_points.append(point_b)
  return BruteFindNearestPoint(point, brute_points)


def Loop(session):
  lap_num = 0
  best_lap = None
  tree = None
  for lap in session.laps:
    lap_num += 1
    # Ignore laps which didn't cross start/finish or unresonably long.
    if lap.duration.ToSeconds() > 0 or lap.duration.ToSeconds() < 120:
      if best_lap:
        print(f'Lap: {lap_num}, num of points: %s' % len(lap.points))
        point_num = -1
        for point in lap.points:
          point_num += 1
          print(point_num)
          brute_closest = BruteFindNearestPoint(point, best_lap.points)
          kdtree_closest = KDTreeSearch(point, best_lap.points, tree)
          if brute_closest != kdtree_closest:
            brute_distance = exit_speed.PointDelta(point, brute_closest)
            kdtree_distance = exit_speed.PointDelta(point, kdtree_closest)
            print(brute_distance, kdtree_distance)
            import pdb; pdb.set_trace()
      if (not best_lap or
          lap.duration.ToNanoseconds() <
          best_lap.duration.ToNanoseconds()):
        best_lap = lap
        x_y_points = []
        for point in lap.points:
          x_y_points.append([point.lon, point.lat])
        tree = cKDTree(np.array(x_y_points), leafsize=10)


def _PrintTiming():
  print(min(BRUTE), max(BRUTE), statistics.median(BRUTE))
  print(min(TIMING), max(TIMING), statistics.median(TIMING))


def main():
  try:
    print('Loading data')
    session = LoadSession()
    print('Done loading')
    Loop(session)
  except (KeyboardInterrupt, SystemExit):
    _PrintTiming()
  _PrintTiming()


if __name__ == '__main__':
  main()
