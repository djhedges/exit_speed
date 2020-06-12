#!/usr/bin/python3

import attr
import log_files
import exit_speed
import statistics
import time
import numpy as np
from scipy.spatial import cKDTree

KDTREE = []
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



@attr.s
class BaseFindClosest(object):
  session = attr.ib()
  best_lap = attr.ib(init=False, default=None)

  def FindNearestPoint(self, point):
    raise NotImplemented

  def UpdateBestLap(self, lap):
    self.best_lap = lap


class BruteForce(BaseFindClosest):
  """Suprisingly not terriable despite O(n^2).

  min - 0.03502225875854492
  max - 0.08478713035583496
  median - 0.03641939163208008
  total run time - 50m52.829s
  """

  @Time(TIMING)
  def FindNearestPoint(self, point):
    nearest_delta = None
    nearest_point = None
    all_deltas = []
    for b_point in self.best_lap.points:
      delta = exit_speed.PointDelta(point, b_point)
      all_deltas.append(delta)
      if not nearest_delta or delta < nearest_delta:
        nearest_delta = delta
        nearest_point = b_point
    return nearest_point


class KDTree(BaseFindClosest):
  """~5x speed up over the BruteForce attempt using cKDTree.

  Building the tree of the best lap.  Not really concerning since this will
  happening while crossing start/finish.
  min - 0.026277780532836914
  max - 0.04867696762084961
  median - 0.02764272689819336

  Finding closest point.
  min - 0.007016181945800781
  max - 0.018321752548217773
  median - 0.0076754093170166016
  total run time - 10m53.250s
  """

  def UpdateBestLap(self, lap):
    super(KDTree, self).UpdateBestLap(lap)
    x_y_points = []
    for point in lap.points:
      x_y_points.append([point.lon, point.lat])
    self.tree = cKDTree(np.array(x_y_points))

  def BruteFindNearestPoint(self, point, best_points):
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

  @Time(KDTREE)
  def FindNearestPoint(self, point):
    _, neighbors = self.tree.query([point.lon, point.lat], 100)
    best_points = []
    for neighbor in neighbors:
      x = self.tree.data[:, 0][neighbor]
      y = self.tree.data[:, 1][neighbor]
      for point_b in self.best_lap.points:
        if point_b.lon == x and point_b.lat == y:
          best_points.append(point_b)
    return self.BruteFindNearestPoint(point, best_points)


def Loop(session):
  brute = BruteForce(session)
  kdtree = KDTree(session)
  lap_num = 0
  for lap in kdtree.session.laps:
    lap_num += 1
    # Ignore laps which didn't cross start/finish or unresonably long.
    if lap.duration.ToSeconds() > 0 or lap.duration.ToSeconds() < 120:
      if kdtree.best_lap:
        print(f'Lap: {lap_num}, num of points: %s' % len(lap.points))
        point_num = 0
        for point in lap.points:
          point_num += 1
          print(point_num)
          brute_closest = brute.FindNearestPoint(point)
          kdtree_closest = kdtree.FindNearestPoint(point)
          if brute_closest != kdtree_closest:
            brute_distance = exit_speed.PointDelta(point, brute_closest)
            kdtree_distance = exit_speed.PointDelta(point, kdtree_closest)
            print(brute_distance, kdtree_distance)
            import pdb; pdb.set_trace()
      if (not kdtree.best_lap or
          lap.duration.ToNanoseconds() <
          kdtree.best_lap.duration.ToNanoseconds()):
        brute.UpdateBestLap(lap)
        kdtree.UpdateBestLap(lap)


def _PrintTiming():
  print(min(KDTREE), max(KDTREE), statistics.median(KDTREE))
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
