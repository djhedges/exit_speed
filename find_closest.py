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


def _LoopIndex(desired_index, best_points):
  if (desired_index < len(best_points) and
      desired_index > -1 * len(best_points) - 1):
    return desired_index
  if desired_index > 0:
    return desired_index % len(best_points)
  else:
    index = len(best_points) - desired_index % len(best_points)
    if index != len(best_points):
      return index
    return 0


def _GoLeftOrRight(point, best_points, start_index, delta):
  left_index = _LoopIndex(start_index - 1, best_points)
  right_index = _LoopIndex(start_index + 1, best_points)
  left_delta = exit_speed.PointDelta(point, best_points[left_index])
  right_delta = exit_speed.PointDelta(point, best_points[right_index])

  if delta < left_delta and delta < right_delta:
    return 0
  if left_delta < right_delta:
    return -1  # Left
  return 1  # Right

@Time(TIMING)
def DoublingSearch(point, point_num, best_points):
  start_index = _LoopIndex(point_num, best_points)
  delta = exit_speed.PointDelta(point, best_points[start_index])
  closet_point = best_points[start_index]
  direction = _GoLeftOrRight(point, best_points, start_index, delta)
  if not direction:
    return closet_point  # Got Lucky

  # Expand
  expansion = 4
  prior_delta = delta
  while True:
    expand_index = _LoopIndex(
        start_index + (expansion * direction), best_points)
    expand_delta = exit_speed.PointDelta(point, best_points[expand_index])
    if expand_delta > prior_delta:
      break
    else:
      prior_delta = expand_delta
      expansion *= 2

  delta = expand_delta
  closest_point = best_points[expand_index]
  if expand_index < start_index:
    points = best_points[expand_index:] + best_points[start_index:]
    return BruteFindNearestPoint(point, points)
  else:
    return BruteFindNearestPoint(point, best_points[start_index:expand_index])

#  # Contract
#  while True:
#    print(list(possible))
#    mid = len(possible) // 2
#    mid_index = _LoopIndex(possible[mid], best_points)
#    mid_delta = exit_speed.PointDelta(point, best_points[mid_index])
#    if mid_delta < delta:
#      delta = mid_delta
#      closet_point = best_points[possible[mid_index]]
#    direction = _GoLeftOrRight(point, best_points, mid_index, mid_delta)
#    if not direction:
#      return closet_point
#    if len(possible) == 1:
#      break
#    if direction == 1:  # Right
#      possible = possible[mid + 1:]
#    else:
#      possible = possible[:mid -1]
#  return closet_point

def Loop(session):
  lap_num = 0
  best_lap = None
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
          doubling_closest = DoublingSearch(point, point_num, best_lap.points)
          if brute_closest != doubling_closest:
            brute_distance = exit_speed.PointDelta(point, brute_closest)
            doubling_distance = exit_speed.PointDelta(point, doubling_closest)
            print(brute_distance, doubling_distance)
            import pdb; pdb.set_trace()
      if (not best_lap or
          lap.duration.ToNanoseconds() <
          best_lap.duration.ToNanoseconds()):
        best_lap = lap


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
