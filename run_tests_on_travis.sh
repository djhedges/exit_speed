#!/bin/bash
for test in "$(ls /home/travis/build/djhedges/exit_speed/*_test.py)"
do
  ./$test
done
