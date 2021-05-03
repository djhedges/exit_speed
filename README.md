# Exit Speed

This is not an officially supported Google product.

## Status

[![Build Status](https://travis-ci.com/djhedges/exit_speed.svg?branch=master)](https://travis-ci.com/github/djhedges/exit_speed)

## Intro

Race car telemetry with a Raspberry Pi.

This project started with a set of LEDs and a USB GPS dongle.  The goal was to
light the LEDs based on the current speed vs the fastest lap of the session.
Hence the name "Exit Speed".  Carrying a higher speed on the exit of a turn is
crucial in the pursuit of faster lap times.

This mimics the behavior of the red/blue triangle in the HUD of GT Sport.
Exit Speed will display green LEDs if the car is faster and red when the car is
slower based on the car's position compared to the fastest lap of the session.

Later a DAQ device was added for measuring and logging voltage from sensors such
as the throttle position and water temperature.  In turn the data was exported
to a Timescale database which allows for real time analysis of the data in
Grafana.  Including lap comparison.

[![4K Demo](https://img.youtube.com/vi/07UoDFVGBuI/0.jpg)](https://youtu.be/07UoDFVGBuI)

[![Image of Green LEDs](https://github.com/djhedges/exit_speed/blob/master/docs/green_led.png)](https://youtu.be/sWjJ_7Hw02U)

Example of data logged at Portland International Raceway being replayed.
[![Replayed Data](http://img.youtube.com/vi/bjZeXXChDv4/0.jpg)](https://youtu.be/bjZeXXChDv4)

Water temperature data logged while on track and tethered to a phone.
![Water Temp](https://github.com/djhedges/exit_speed/blob/master/docs/water_temp.png)

Lap comparison examples.  Total hack atm but a work in progress.
![Speed](https://github.com/djhedges/exit_speed/blob/master/docs/lap_comparison_speed.png)
![TPS](https://github.com/djhedges/exit_speed/blob/master/docs/lap_comparison_tps_voltage.png)

## Hardware

### Adafruit DotStar LEDs

The Adafruit DotStar LEDs can be trimmed to a desired length and provide ample
brightness for use in a race car.
https://www.adafruit.com/product/2241

### ADXL345

A ADXL345 accelerometer is used to measure the g forces experienced by the car.
Calibration was done following the Sparkfun guide to set the min/max values.
I need to take the extra time to read the specsheets to see if there is a more
accurate way to calibrate the ADXL345.  I read somewhere about a sine instead
of linear.
https://learn.sparkfun.com/tutorials/adxl345-hookup-guide#calibration

### UBlox 8

The USB GPS dongle used is GNSS100L.  It is based on the UBlox 8 chipset which
is very well documented.  Note you'll want to bump the output rate of the device
to 10hz based on the UBX-CFG-RATE setting.  This can be done with the Ublox
window software can be set to persist between power cycles.  There were a
couple of other settings that seem reasonable to change as well so I recommend
reading the manual.  Unfortunately it's been several months since I initial
setup the device and I no longer recall what the other settings were.
http://canadagps.com/GNSS100L.html
https://www.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_%28UBX-13003221%29.pdf
`Bus 001 Device 007: ID 1546:01a8 U-Blox AG [u-blox 8]`

### Labjack U3

For converting analog voltages to digtial a Labjack U3 device as chosen based on
the documentation, API, examples and awesome support.  There are cheaper DAQ
devices out there however the U3 also supports high voltage readings (0-10v on
AIN-0-4 inputs).
https://labjack.com/products/u3

They also sell voltage dividers to drop high voltages down to the acceptable low
voltage range of 0-2.4v or 0-3.6v for the FIO4-EIO7 inputs.
https://labjack.com/accessories/ljtick-divider

It's worth noting the options for grounding the U3.  We ran a ground from the
SGND inputs.
https://labjack.com/support/datasheets/u3/hardware-description/ain/analog-input-connections/signal-powered-externally

### WBO2

The car I have came with an older WBO 2A0/2A1 device with a LD01 display for the
air fuel ratio.  Luckily the logging format of the devcie's terminal output is
well documented.  The wide band device also supports logging of 3 additional
5v sensors and 3 thermocouple inputs.
http://wbo2.com/2a0/default.htm

## Software Design Choices

Python has suprisingly been able to keep up with the GPS 10hz output.  Ideally
this should be rewritten in Go or C++.

I've always wanted to play with the multriprocessing module and it has proved
useful.  For example the metrics which are uploaded to Timescale are done in a
seperate process.  This isolates the main process from unexpected errors and
delays on I/O operations.  The Labjack and WBO2 readings also take place in
seperate processes as well.

### Crossing Start/Finish

Exit Speed has a map of tracks in the NW with GPS locations of arbitrary
start/finish points selected from Google maps.   The ExitSpeed class is
initialized with a start_finish_range which determines how close the car needs
to be to the finish line before we consider the lap complete.  Without the range
limit points on far ends of the track would have counted as crossing
start/finish.

Once the car is within range triangles are created consisting of two points
along the straight away and the start/finish point from the prior mapping.
When the older of the two points obtuse (greater than 90 degress) it is
determined that the car has crossed start/finish.  The older point becomes the
first and last point of a lap.

### Lap Timing

To improve upon lap time calculation a bit of trigonometry and physics is used
to calculate a laptime with a resolution of thousands of a seconds despite the
10hz GPS refresh.  Accuracy during testing was within ±0.022 seconds while on
average being off by only 0.008 seconds compared to the transponder timing from
a race.

We start by calcuating the distance between B & C and from B to start/finish
and C to start/finish.  Knowing the 3 sides of the triangle we're able to
deterimine the angle of B.

The timing between points C & B is 0.1 seconds and we know the speed at
points B & C.  This allows us to calcuate the acceleration between points B & C.
Next we can calcuate the distance from point B to when the car actually crosses the start finish line.

Finally we take the time between the first and last points of a lap and subtract
the time it take for the car to travel from start/finish to point C.  Finally add the time it took on the prior lap for the car to travel from start/finish to
point C.

```
point_c |\
        | \
        |  \
        |   \
        |____\______ start/finish
        |    /
        |   /
        |  /
        |B/
point_b |/
```

Comparison of transponder lap times vs Exit Speed lap times.

|Transponder | Exit Speed | Deltas|
|------------|------------|-------|
|1:36.530	   | 1:36.508	  | 0.022 |
|1:32.029	   | 1:32.020	  | 0.009 |
|1:32.149	   | 1:32.144	  | 0.005 |
|1:31.832	   | 1:31.838	  | 0.006 |
|1:30.893	   | 1:30.884	  | 0.009 |
|1:31.422	   | 1:31.417	  | 0.005 |
|1:31.500	   | 1:31.510	  | 0.010 |
|1:33.516	   | 1:33.499	  | 0.017 |
|1:32.415	   | 1:32.428	  | 0.013 |
|1:31.665	   | 1:31.658	  | 0.007 |
|1:31.075	   | 1:31.076	  | 0.001 |
|1:31.271	   | 1:31.270	  | 0.001 |
|1:30.932	   | 1:30.930	  | 0.002 |
|1:31.504	   | 1:31.508	  | 0.004 |

### Speed Deltas (LEDs)

For the fastest lap a BallTree is constructed of GPS coordinates for the lap.
On the current lap each GPS point's speed is compared against the closest point of the best lap by searching the BallTree.  The delta of the speed of these
points are stored in a collections.deque which holds the last 10 points.  If the
median of the points are faster then the LEDs are set to green.  If slower
they're set to red.
https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.BallTree.html

Another way to put it is if the median speed of the last second is faster set
the LEDs to green.  Else red.

Earlier versions experimented with updating the LEDs more often as well as
having a ratio of LEDs lit based on the size of the speed delta.  But having
LEDs flicker all the time can be distracting.  Also GPS inaccuracies can lead to
misleading results.  I find it's best to glance at the LEDs on the straights.

Here is an example of the LEDs in action.
https://youtu.be/sWjJ_7Hw02U

### Grafana & Timescale

Initially Prometheus and InfluxDB were tested before settling on Timescale.
Grafana is designed for displaying time series data which is great for live or
replayed data.  However that made graph lap comparisons difficult.  Since
Timescale is backed by PostgresSQL I was able to come up with some clever
Grafana queries to overlay laps.  It sounds like Grafana plans to add support
for graphing none time series data in the future.
https://youtu.be/2FHSHHTeZAU
https://youtu.be/joWSMB6zanM

## Installation & Setup

### GPS

This going off memory but I believe I downloaded the u-center software from Ublox.
https://www.u-blox.com/en/product/u-center

Then modified the following settings:

*   UBX-CFG-RATE  # 10hz
*   UBX-CFG-CFG   # Save the config so it persists after a power cycle.
*   TODO: Document other settings that might be usefull.

External documentation on setting the 10hz rate.
https://gpswebshop.com/blogs/tech-support-by-vendors-stoton/how-to-change-the-gnss100l-or-gnss200l-usb-gps-update-rate-to-10hz/

### Raspberry Pi

```
sudo apt-get install gfortran libatlas3-base libblas-dev libgfortran5 liblapack-dev python3 pip3
pip3 install -r requirements.txt
```

If you run into issues I would take a look at the travis config for pointers.
Travis used to build and run unittests from a clean environment on each change
and weekly.
https://github.com/djhedges/exit_speed/blob/master/.travis.yml

### Labjack

If your setup is using a Labjack for measuring sensors you'll need to install
the Exodrivers.
https://labjack.com/support/software/installers/exodriver

## Examples & Usage

### Config

My current config is checked in as corrado.yaml.  It provides mapping between
inputs to point proto fields.  By removing `labjack:` or `wbo2:` from the config
the corresponding subprocesses are disabled.

```
leds: True
timescale: True
labjack:
  ain0: fuel_level_voltage
  ain1: water_temp_voltage
  ain2: oil_pressure_voltage
wbo2:
  lambda_16: afr
  rpm_count: rpm
  user_3: tps_voltage
```

### Flags

```
./exit_speed.py --helpfull

./exit_speed.py:
  --data_log_path: The directory to save data and logs.
    (default: '/home/pi/lap_logs')

config_lib:
  --config_path: The location of the Exit Speed config.
    (default: './etc/corrado.yaml')

leds:
  --led_brightness: Percentage of how bright the LEDs are. IE 0.5 == 50%.
    (default: '0.5')
    (a number)
  --led_update_interval: Limits how often the LEDs are able to change to prevent
    excessive flickering.
    (default: '0.2')
    (a number)
  --speed_deltas: Used to smooth out GPS data.  This controls how many recent
    speed deltas are stored.  50 at 10hz means a median of the last 5 seconds is
    used.
    (default: '10')
    (an integer)

timescale:
  --commit_cycle: Number of points to commit at a time.
    (default: '3')
    (an integer)
  --timescale_db_spec: Postgres URI connection string.
    (default: 'postgres://exit_speed:faster@cloud:/exit_speed')

wbo2:
  --cylinders: Number of cylinders in the engine.
    (default: '6')
    (an integer)
  --stoichiometric: This is used to convert the Lambda_16 bytes into an A/F
    ratio. This should be changed based on fuel.Petrol 14.7, LGP 15.5, Methanol
    6.4, Diesel 14.5
    (default: '14.7')
    (a number)
```

### Examples

#### exit_speed.py

Starts Exit Speed and logs to stderr.

```
./exit_speed.py --log_dir ~/lap_logs/ --config_path=./etc/corrado.yaml \
  --alsologtostderr
```

Quick and dirty way to start Exit Speed on boot is by adding the following to
`/etc/rc.local`.  You can than connect to the screen session with `screen -rd`.

```
su - pi -c "screen -S exit_speed -dm /home/pi/git/exit_speed/exit_speed.py \
  --log_dir ~/lap_logs/ --config_path=/home/pi/git/exit_speed/etc/corrado.yaml \
  --alsologtostderr" &
```

#### replay_data.py

Exit Speed logs points to `--log_dir` in files ending in `.data` such as
`2020-09-24T12:57:12.500000_1.data`.  The data files can be replayed which
into to Timescale.

```
./replay_data.py ~/lap_logs/2020-09-24T12\:57\:12.500000_1.data \
  --include_sleep=False
```

If `--include_sleep=True` is set then delays are added to mimic as if the
replayed data was being recorded in real time.  `--include_sleep=True` also tags
the data as "replayed" instead of "live" and is removed by cleanup_timescale.py.

#### cleanup_timescale.py

cleanup_timescale.py is used to reduce the number of laps stored in Timescale.

```
./cleanup_timescale.py --max_lap_duration_ms=180000 --min_lap_duration_ms=60000
```
