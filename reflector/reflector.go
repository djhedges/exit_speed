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
	"google.golang.org/grpc"
	gpspb "github.com/djhedges/exit_speed/gps_go_proto"
)

func A() string {
  return "test"
}

type reflect struct {
	gpspb.UnimplementedReflectServer
}

func (s *reflect) ExportPoint(ctx context.Context, in *gpspb.PointUpdate) (*gpspb.Response, error) {
	log.Printf('I haz a point')
	return &gpspb.Response{}, nil
}

func main() {
	lis, err := net.Listen("tcp", 65000)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	s := grpc.NewServer()
	gpspb.RegisterReflectServer(s, &reflect{})
	if err := s.Serve(lis); err != nil {
		log.Fataf("Failed to serve: %v", err)
	}
}
