load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
  name = "main",
  srcs = ["main.py"],
  deps = [":accelerometer",
					":common_lib",
					":config_lib",
					":exit_speed_proto",
					":gps_sensor",
					":gyroscope",
					":labjack",
					":lap_lib",
					":leds",
					":postgres",
					":tire_temperature",
					":wbo2",
					"//exit_speed/tracks"
					]
)

py_library(
  name = "exit_speed_proto",
  srcs = ["exit_speed_pb2.py"],
)

py_library(
  name = "accelerometer",
  srcs = ["accelerometer.py"],
  deps = [":exit_speed_proto",
					":sensor",
					]
)

py_library(
  name = "common_lib",
  srcs = ["common_lib.py"],
  deps = [":exit_speed_proto",
					"//exit_speed/tracks",
					]
)

py_library(
  name = "config_lib",
  srcs = ["config_lib.py"],
)

py_library(
  name = "data_logger",
  srcs = ["data_logger.py"],
)

py_library(
  name = "gps_sensor",
  srcs = ["gps_sensor.py"],
  deps = [":exit_speed_proto",
					":sensor",
					]
)

py_library(
  name = "gyroscope",
  srcs = ["gyroscope.py"],
  deps = [":exit_speed_proto",
					":sensor",
					]
)

py_library(
  name = "labjack",
  srcs = ["labjack.py"],
  deps = [":exit_speed_proto",
					":sensor",
					]
)

py_library(
  name = "lap_lib",
  srcs = ["lap_lib.py"],
  deps = [":common_lib",
					":exit_speed_proto",
					"//exit_speed/tracks",
					]
)

py_library(
  name = "leds",
  srcs = ["leds.py"],
  deps = [":exit_speed_proto"],
)

py_library(
  name = "postgres",
  srcs = ["postgres.py"],
  deps = [":common_lib",
					":exit_speed_proto",
					]
)

py_library(
  name = "sensor",
  srcs = ["sensor.py"],
  deps = [":common_lib",
					":data_logger",
					":exit_speed_proto",
					":postgres",
					]
)

py_library(
  name = "tire_temperature",
  srcs = ["tire_temperature.py"],
  deps = [":common_lib",
					":exit_speed_proto",
					":sensor",
					]
)

py_library(
  name = "wbo2",
  srcs = ["wbo2.py"],
  deps = [":exit_speed_proto",
					":sensor",
					]
)
