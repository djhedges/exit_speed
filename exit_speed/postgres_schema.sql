CREATE TABLE gps (
  time                         TIMESTAMPTZ       NOT NULL,
  lat                          FLOAT             NOT NULL,
  lon                          FLOAT             NOT NULL,
  alt                          FLOAT             NOT NULL,
  speed_ms                     FLOAT             NOT NULL
);

CREATE TABLE accelerometer (
  time                         TIMESTAMPTZ       NOT NULL,
  accelerometer_x              FLOAT             NOT NULL,
  accelerometer_y              FLOAT             NOT NULL,
  accelerometer_z              FLOAT             NOT NULL
);

CREATE TABLE gyroscope (
  time                         TIMESTAMPTZ       NOT NULL,
  gyro_x                       FLOAT             NOT NULL,
  gyro_y                       FLOAT             NOT NULL,
  gyro_z                       FLOAT             NOT NULL
);

CREATE TABLE labjack (
  time                         TIMESTAMPTZ       NOT NULL,
  labjack_temp_f               FLOAT             NOT NULL,
  battery_voltage              FLOAT,
  front_brake_pressure_voltage FLOAT,
  fuel_level_voltage           FLOAT,
  fuel_pressure_voltage        FLOAT,
  oil_pressure_voltage         FLOAT,
  oil_temp_voltage             FLOAT,
  rear_brake_pressure_voltage  FLOAT,
  water_temp_voltage           FLOAT
);

CREATE TABLE wbo2 (
  time                         TIMESTAMPTZ       NOT NULL,
  afr                          FLOAT             NOT NULL,
  rpm                          INT               NOT NULL,
  tps_voltage                  FLOAT
);
CREATE TABLE sessions(
  id               SERIAL            PRIMARY KEY,
  time                         TIMESTAMPTZ       NOT NULL,
  track            TEXT              NOT NULL,
  car              TEXT              NOT NULL,
  live_data        BOOLEAN           DEFAULT TRUE
);
CREATE TABLE laps(
  id               SERIAL            PRIMARY KEY,
  session_id       INT               REFERENCES sessions (id),
  number           INT               NOT NULL,
  start_time                         TIMESTAMPTZ       NOT NULL,
  end_time                           TIMESTAMPTZ
);
