#!/bin/bash
set -ex
python3 -m exit_speed.accelerometer_test
python3 -m exit_speed.common_lib_test
python3 -m exit_speed.data_logger_test
python3 -m exit_speed.gyroscope_test
python3 -m exit_speed.import_data_test
python3 -m exit_speed.labjack_test
python3 -m exit_speed.lap_lib_test
python3 -m exit_speed.leds_test
python3 -m exit_speed.main_test
python3 -m exit_speed.postgres_test
python3 -m exit_speed.sensor_test
python3 -m exit_speed.tire_temperature_test
python3 -m exit_speed.tracks_test
python3 -m exit_speed.wbo2_test
