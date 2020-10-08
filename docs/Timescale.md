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
                          'Pacific Raceway',
                          'Spokane Raceway');
CREATE TABLE sessions(
  id               SERIAL            PRIMARY KEY,
  time             TIMESTAMPTZ       NOT NULL,
  track            track             NOT NULL,
  car              TEXT              NOT NULL,
  live_data        BOOLEAN           DEFAULT TRUE
);
CREATE TABLE laps(
  id               SERIAL            PRIMARY KEY,
  session_id       INT               REFERENCES sessions (id),
  number           INT               NOT NULL,
  duration_ms      INT
);
CREATE TABLE points (
  time                  TIMESTAMPTZ       NOT NULL,
  session_id            INT               REFERENCES sessions (id),
  lap_id                INT               REFERENCES laps (id),
  lat                   FLOAT             NOT NULL,
  lon                   FLOAT             NOT NULL,
  alt                   FLOAT             NOT NULL,
  speed                 FLOAT             NOT NULL,
  geohash               TEXT              NOT NULL,
  elapsed_duration_ms   INT               NOT NULL,
  tps_voltage           FLOAT,
  water_temp_voltage    FLOAT,
  oil_pressure_voltage  FLOAT,
  rpm                   FLOAT,
  afr                   FLOAT,
  fuel_level_voltage    FLOAT
);
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
SELECT create_hypertable('points', 'time');
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

## Allow connections from the Pi

Add the following to the end of `/etc/postgresql/12/main/pg_hba.conf`

```
host    exit_speed      all             10.3.1.3/32             md5
```

Modify the following in `/etc/postgresql/12/main/postgresql.conf`

```
listen_addresses = 'localhost,10.3.1.1'
```

Finally restart with `sudo service postgresql restart`
