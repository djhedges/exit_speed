#!/usr/bin/python3

import attr
import log_files
import exit_speed
import statistics
import time

TIMING = []

def Time(func):
  def timed(*args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    run_time = time.time() - start
    TIMING.append(run_time)
    return result
  return timed


def LoadSession():
  return log_files.ReadLog('testdata/data-2019-08-18T16:53:01.250Z')


@attr.s
class BruteForce(object):
  """Suprisingly not terriable despite O(n^2).

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
  min - 0.03502225875854492
  max - 0.08478713035583496
  median - 0.03641939163208008
  """
  session = attr.ib()
  best_lap = attr.ib(init=False, default=None)

  @Time
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
    speed_delta = point.speed - nearest_point.speed

  def Process(self, lap):
    for point in lap.points:
      self.FindNearestPoint(point)

  def Loop(self):
    lap_num = 0
    for lap in self.session.laps:
      lap_num += 1
      # Ignore laps which didn't cross start/finish or unresonably long.
      if lap.duration.ToSeconds() > 0 or lap.duration.ToSeconds() < 120:
        if (not self.best_lap or
            lap.duration.ToNanoseconds() < self.best_lap.duration.ToNanoseconds()):
          self.best_lap = lap
        print(f'Lap: {lap_num}, num of points: %s' % len(lap.points))
        self.Process(lap)


def main():
  try:
    print('Loading data')
    session = LoadSession()
    print('Done loading')
    brute = BruteForce(session)
    brute.Loop()
  except (KeyboardInterrupt, SystemExit):
    print(min(TIMING), max(TIMING), statistics.median(TIMING))
  print(min(TIMING), max(TIMING), statistics.median(TIMING))

if __name__ == '__main__':
  main()
