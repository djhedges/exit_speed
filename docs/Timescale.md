# Notes for setting up Timescale


## Remote Timescale Setup

This was done on Debian GNU/Linux 10 (buster) on a remote server.

Install mostly consists of following the steps here.
https://docs.timescale.com/latest/getting-started/installation/debian/installation-apt-debian


### Create database and tables

Connect to the database with `sudo -u postgres psql postgres`

Then run the following statements:

```
CREATE DATABASE exit_speed;
\c exit_speed;
CREATE TYPE track AS ENUM('Test Parking Lot',
                          'Oregon Raceway Park',
                          'Portland International Raceway',
                          'The Ridge Motorsport Park',
                          'Pacific Raceways',
                          'Spokane Raceway');
CREATE TYPE car AS ENUM('Corrado', 'Civic');
CREATE TABLE sessions(
  id               SERIAL            PRIMARY KEY,
  time             TIMESTAMPTZ       NOT NULL,
  track            track             NOT NULL,
  car              car               NOT NULL,
  live_data        BOOLEAN           DEFAULT TRUE
);
CREATE TABLE laps(
  id               SERIAL            PRIMARY KEY,
  session_id       INT               REFERENCES sessions (id),
  number           INT               NOT NULL,
  duration_ms      INT
);
CREATE TABLE points (
  time                         TIMESTAMPTZ       NOT NULL,
  session_id                   INT               REFERENCES sessions (id),
  lap_id                       INT               REFERENCES laps (id),
  lat                          FLOAT             NOT NULL,
  lon                          FLOAT             NOT NULL,
  alt                          FLOAT             NOT NULL,
  speed                        FLOAT             NOT NULL,
  geohash                      TEXT              NOT NULL,
  elapsed_duration_ms          INT               NOT NULL,
  elapsed_distance_m           FLOAT             NOT NULL,
  tps_voltage                  FLOAT,
  water_temp_voltage           FLOAT,
  oil_pressure_voltage         FLOAT,
  rpm                          FLOAT,
  afr                          FLOAT,
  fuel_level_voltage           FLOAT,
  accelerometer_x              FLOAT,
  accelerometer_y              FLOAT,
  accelerometer_z              FLOAT,
  pitch                        FLOAT,
  roll                         FLOAT,
  gyro_x                       FLOAT,
  gyro_y                       FLOAT,
  gyro_z                       FLOAT,
  front_brake_pressure_voltage FLOAT,
  rear_brake_pressure_voltage  FLOAT,
  battery_voltage              FLOAT,
  oil_temp_voltage             FLOAT,
  labjack_temp_f               FLOAT,
  lf_tire_temp_inner           FLOAT,
  lf_tire_temp_middle          FLOAT,
  lf_tire_temp_outer           FLOAT,
  rf_tire_temp_inner           FLOAT,
  rf_tire_temp_middle          FLOAT,
  rf_tire_temp_outer           FLOAT,
  lr_tire_temp_inner           FLOAT,
  lr_tire_temp_middle          FLOAT,
  lr_tire_temp_outer           FLOAT,
  rr_tire_temp_inner           FLOAT,
  rr_tire_temp_middle          FLOAT,
  rr_tire_temp_outer           FLOAT,
  fuel_pressure_voltage        FLOAT
);
EXIT;
```

## Add a database user.

```
sudo -u postgres psql postgres -d exit_speed
CREATE USER exit_speed WITH PASSWORD 'faster';
GRANT ALL PRIVILEGES ON DATABASE exit_speed TO exit_speed;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO exit_speed;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO exit_speed;
EXIT;
```

### Replication Notes (Likely incomplete)

Streaming replication is not possible between different architectures.
Logical replication is doable but not for a hypertable.  I guesss we're not really using timescale anymore are we?

On the pi
```
sudo -u postgres psql postgres -d exit_speed
CREATE USER repuser WITH PASSWORD 'faster';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO repuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO repuser;
CREATE PUBLICATION exit_speed_publication FOR ALL TABLES;
ALTER TABLE sessions REPLICA IDENTITY FULL;
ALTER TABLE laps REPLICA IDENTITY FULL;
ALTER TABLE points REPLICA IDENTITY FULL;
```

## Allow connections to the Pi

Add the following to the end of `/etc/postgresql/11/main/pg_hba.conf`

```
host    repuser all             10.3.1.1/32             md5
```

Modify the following in `/etc/postgresql/11/main/postgresql.conf`

```
wal_level = logical
listen_addresses = 'localhost,10.3.1.3'
```

Finally restart with `sudo service postgresql restart`

## On the replicas

Manually
* Create the tables (they won't be created by the subscription)
* Create the user exit_speed for grafana
* Future schema changes will have to be made on the replicas manually

```
CREATE SUBSCRIPTION exit_speed_subscription CONNECTION 'host=10.3.1.3 port=5432 password=faster user=repuser dbname=exit_speed' PUBLICATION exit_speed_publication;
```

## Troubleshooting Notes

On the pi view replication slots

```
SELECT * FROM pg_replication_slots;
```

Postgresql logs

```
/var/log/postgresql/postgresql-11-main.log
```
