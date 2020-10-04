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
	reflectorpb "github.com/djhedges/exit_speed/reflector_go_proto"
)

func A() string {
  return "test"
}

type reflect struct {
	reflectorpb.UnimplementedReflectServer
	point_queue []reflectorpb.PointUpdate
}

// Get the oldest point from point_queue based on the points GPS time.
func (r *reflect) GetPoint() reflectorpb.PointUpdate {
	var latest reflectorpb.PointUpdate
	for i, point_update := range r.point_queue {
		if (latest == nil || point_update.Point.Time < latest.Point.Time) {
			latest = point_update
		}
	}
	return latest
}

func (r *reflect) ExportPoint(ctx context.Context, req *reflectorpb.PointUpdate) (*reflectorpb.Response, error) {
	r.point_queue = append(r.point_queue, *req)
	return &reflectorpb.Response{}, nil
}
