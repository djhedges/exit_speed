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

  After a few laps the timing was min 0.03, max 0.06 and median 0.04 seconds.
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
