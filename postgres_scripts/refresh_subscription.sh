#!/bin/bash
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SCHEMA_FILE="$SCRIPT_DIR/../exit_speed/postgres_schema.sql"
DB_NAME="exit_speed"
SUBSCRIPTION_NAME="exit_speed"
PUBLICATION_NAME="alien"
CONNINFO="host=exitspeed.tail0ae7d.ts.net port=5432 user=postgres password=faster dbname=exit_speed"

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
EOF

sudo -u postgres psql -d $DB_NAME <<EOF
CREATE SUBSCRIPTION $SUBSCRIPTION_NAME 
CONNECTION '$CONNINFO' 
PUBLICATION $PUBLICATION_NAME;
EOF
