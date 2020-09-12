# Notes for setting up Timescale

This was done on Debian GNU/Linux 10 (buster).

## Install Timescale and Postgres

Install mostly consists of following the steps here.
https://docs.timescale.com/latest/getting-started/installation/debian/installation-apt-debian

```
sudo apt-get install wget
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -c -s)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/debian/ `lsb_release -c -s` main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt-get update

# Now install appropriate package for PG version
sudo apt-get install timescaledb-postgresql-12
sudo timescaledb-tune --quiet --yes
sudo service postgresql restart
```

## Create database and tables

Connect to the database with `sudo -u postgres psql postgres`

Then run the following statements:

```
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
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
  alt                   TEXT              NOT NULL,
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
SELECT create_hypertable('points', 'time');
```
