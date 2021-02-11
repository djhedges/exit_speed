//!/usr/bin/python3
// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Golang implementation for exporting data to Timescale.
package reflector

import (
	"context"
	"database/sql"
	reflectorpb "github.com/djhedges/exit_speed/reflector_go_proto"
	_ "github.com/lib/pq"
	"log"
)

func A() string {
	return "test"
}

type reflect struct {
	reflectorpb.UnimplementedReflectServer
	point_channel chan reflectorpb.PointUpdate
}

const (
	POINT_PREPARE = `
PREPARE point_insert AS
INSERT INTO points (time, session_id, lap_id, lat, lon, alt, speed, geohash,
                    elapsed_duration_ms, tps_voltage, water_temp_voltage,
                    oil_pressure_voltage, rpm, afr, fuel_level_voltage,
                    accelerometer_x, accelerometer_y, accelerometer_z, pitch,
                    roll)
VALUES ($1, $2, $3, $4, $5,
        $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15,
        $16, $17, $18, $19, $20,
			  $21, $22, $23)
`
	POINT_INSERT = `
EXECUTE point_insert (%s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
										  %s, %s, %s)
`
)

func (r *reflect) ExportPoint(ctx context.Context, req *reflectorpb.PointUpdate) (*reflectorpb.Response, error) {
	r.point_channel <- *req
	return &reflectorpb.Response{}, nil
}

func (r *reflect) TimescaleExportPoint() {
	db, err := sql.Open("postgres", "postgres://exit_speed:faster@cloud:/exit_speed")
	if err != nil {
		log.Fatal(err)
	}
	db.QueryRow(POINT_PREPARE)
	for {
		point_update := <-r.point_channel
		db.QueryRow(POINT_INSERT,
			point_update.Point.Time,
			point_update.SessionId,
			point_update.LapId,
			point_update.Point.Lat,
			point_update.Point.Lon,
			point_update.Point.Alt,
			point_update.Point.Speed*2.23694, // m/s to mph,
			point_update.Point.Geohash,
			point_update.ElapsedDurationMs,
			point_update.Point.TpsVoltage,
			point_update.Point.WaterTempVoltage,
			point_update.Point.OilPressureVoltage,
			point_update.Point.Rpm,
			point_update.Point.Afr,
			point_update.Point.FuelLevelVoltage,
			point_update.Point.AccelerometerX,
			point_update.Point.AccelerometerY,
			point_update.Point.AccelerometerZ,
			point_update.Point.Pitch,
			point_update.Point.Roll,
			point_update.Point.GyroX,
			point_update.Point.GyroY,
			point_update.Point.GyroZ)
	}
}
