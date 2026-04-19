#!/bin/bash
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SCHEMA_FILE="$SCRIPT_DIR/../exit_speed/postgres_schema.sql"
DB_NAME="exit_speed"
PUBLICATION_NAME="alien"
LAP_LOG_PATH="/home/pi/lap_logs"

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "Error: Schema file $SCHEMA_FILE not found."
  exit 1
fi

sudo -u postgres psql postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

sudo -u postgres psql -d $DB_NAME -f "$SCHEMA_FILE"

sudo -u postgres psql -d $DB_NAME <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'exit_speed') THEN
        CREATE ROLE exit_speed WITH LOGIN PASSWORD 'faster';
    END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO exit_speed;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO exit_speed;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO exit_speed;

DROP PUBLICATION IF EXISTS $PUBLICATION_NAME;
CREATE PUBLICATION $PUBLICATION_NAME FOR ALL TABLES;

ALTER TABLE gps REPLICA IDENTITY FULL;
ALTER TABLE accelerometer REPLICA IDENTITY FULL;
ALTER TABLE gyroscope REPLICA IDENTITY FULL;
ALTER TABLE labjack REPLICA IDENTITY FULL;
ALTER TABLE wbo2 REPLICA IDENTITY FULL;
ALTER TABLE ecu REPLICA IDENTITY FULL;
ALTER TABLE egts REPLICA IDENTITY FULL;
ALTER TABLE pdm REPLICA IDENTITY FULL;
ALTER TABLE sessions REPLICA IDENTITY FULL;
ALTER TABLE laps REPLICA IDENTITY FULL;
EOF

for car in "$LAP_LOG_PATH"/*; do
  [ -d "$car" ] || continue
  for track in "$car"/*; do
    [ -d "$track" ] || continue
    for session in "$track"/*; do
      [ -d "$session" ] || continue
      echo "Importing $session"
      python3 -m exit_speed.import_data --data_dir "$session" --alsologtostderr
    done
  done
done
