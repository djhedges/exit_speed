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
CREATE TABLE ecu (
  time                         TIMESTAMPTZ       NOT NULL,
  rpm                          FLOAT             NOT NULL,
  map_psi                      FLOAT             NOT NULL,
  mgp_psi                      FLOAT             NOT NULL,
  barometric_pressure_psi      FLOAT             NOT NULL,
  tps                          FLOAT             NOT NULL,
  injector_dc                  FLOAT             NOT NULL,
  injector_dc_sec              FLOAT             NOT NULL,
  injector_pulse_width         FLOAT             NOT NULL,
  ect_f                        FLOAT             NOT NULL,
  iat_f                        FLOAT             NOT NULL,
  ecu_volts                    FLOAT             NOT NULL,
  maf                          FLOAT             NOT NULL,
  gear_position                INT               NOT NULL,
  injector_timing              FLOAT             NOT NULL,
  ignition_timing              FLOAT             NOT NULL,
  lambda_1                     FLOAT             NOT NULL,
  trig_1_error_counter         INT               NOT NULL,
  fault_codes                  INT               NOT NULL,
  fuel_pressure_psi            FLOAT             NOT NULL,
  oil_temp_f                   FLOAT             NOT NULL,
  oil_pressure_psi             FLOAT             NOT NULL,
  knock_level_1                FLOAT             NOT NULL,
  knock_level_2                FLOAT             NOT NULL,
  front_brake_pressure_psi     FLOAT             NOT NULL,
  rear_brake_pressure_psi      FLOAT             NOT NULL
);
CREATE TABLE egts (
  time                         TIMESTAMPTZ       NOT NULL,
  egt_1_f                      FLOAT             NOT NULL,
  egt_2_f                      FLOAT             NOT NULL,
  egt_3_f                      FLOAT             NOT NULL,
  egt_4_f                      FLOAT             NOT NULL,
  egt_5_f                      FLOAT             NOT NULL,
  egt_6_f                      FLOAT             NOT NULL
);
CREATE TABLE pdm (
  time                         TIMESTAMPTZ       NOT NULL,
  hp_output_1_status           INT               NOT NULL,
  hp_output_1_freq             INT               NOT NULL,
  hp_output_1_duty_cycle       FLOAT             NOT NULL,
  hp_output_1_current          FLOAT             NOT NULL,
  hp_output_2_status           INT               NOT NULL,
  hp_output_2_freq             INT               NOT NULL,
  hp_output_2_duty_cycle       FLOAT             NOT NULL,
  hp_output_2_current          FLOAT             NOT NULL,
  hp_output_3_status           INT               NOT NULL,
  hp_output_3_freq             INT               NOT NULL,
  hp_output_3_duty_cycle       FLOAT             NOT NULL,
  hp_output_3_current          FLOAT             NOT NULL,
  hp_output_4_status           INT               NOT NULL,
  hp_output_4_freq             INT               NOT NULL,
  hp_output_4_duty_cycle       FLOAT             NOT NULL,
  hp_output_4_current          FLOAT             NOT NULL,
  adio_1_status                INT               NOT NULL,
  adio_1_freq                  INT               NOT NULL,
  adio_1_duty_cycle            FLOAT             NOT NULL,
  adio_1_voltage               FLOAT             NOT NULL,
  adio_2_status                INT               NOT NULL,
  adio_2_freq                  INT               NOT NULL,
  adio_2_duty_cycle            FLOAT             NOT NULL,
  adio_2_voltage               FLOAT             NOT NULL,
  adio_3_status                INT               NOT NULL,
  adio_3_freq                  INT               NOT NULL,
  adio_3_duty_cycle            FLOAT             NOT NULL,
  adio_3_voltage               FLOAT             NOT NULL,
  adio_4_status                INT               NOT NULL,
  adio_4_freq                  INT               NOT NULL,
  adio_4_duty_cycle            FLOAT             NOT NULL,
  adio_4_voltage               FLOAT             NOT NULL,
  adio_5_status                INT               NOT NULL,
  adio_5_freq                  INT               NOT NULL,
  adio_5_duty_cycle            FLOAT             NOT NULL,
  adio_5_voltage               FLOAT             NOT NULL,
  adio_6_status                INT               NOT NULL,
  adio_6_freq                  INT               NOT NULL,
  adio_6_duty_cycle            FLOAT             NOT NULL,
  adio_6_voltage               FLOAT             NOT NULL,
  adio_7_status                INT               NOT NULL,
  adio_7_freq                  INT               NOT NULL,
  adio_7_duty_cycle            FLOAT             NOT NULL,
  adio_7_voltage               FLOAT             NOT NULL,
  adio_8_status                INT               NOT NULL,
  adio_8_freq                  INT               NOT NULL,
  adio_8_duty_cycle            FLOAT             NOT NULL,
  adio_8_voltage               FLOAT             NOT NULL,
  pdm_temp_f                   FLOAT             NOT NULL,
  pdm_voltage                  FLOAT             NOT NULL
);
CREATE TABLE sessions(
  id               SERIAL            PRIMARY KEY,
  time             TIMESTAMPTZ       NOT NULL,
  track            TEXT              NOT NULL,
  car              TEXT              NOT NULL,
  live_data        BOOLEAN           DEFAULT TRUE
);
CREATE TABLE laps(
  session_id       INT               REFERENCES sessions (id),
  number           INT               NOT NULL,
  start_time       TIMESTAMPTZ       NOT NULL,
  end_time         TIMESTAMPTZ,
  duration_ns      BIGINT,
  PRIMARY KEY (session_id, number)
);
