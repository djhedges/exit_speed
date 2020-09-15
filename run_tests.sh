#!/bin/bash
for test in "$(ls /home/travis/build/djhedges/exit_speed/*_test.py)"
do
  python3 $test
done
