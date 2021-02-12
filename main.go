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

package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"google.golang.org/grpc"
	"github.com/djhedges/exit_speed/reflector"
	reflectorpb "github.com/djhedges/exit_speed/reflector_go_proto"
)


const (
	socket = "/tmp/exit_speed.sock"
)

func main() {
	var db_spec string
	flag.StringVar(&db_spec,
	               "timescale_db_spec",
	               "postgres://exit_speed:faster@cloud:/exit_speed",
                 "Postgres URI connection string")
	flag.Parse()
  log.Printf("timescale_db_spec=%s", db_spec)
	_, err := os.Stat(socket)
  if err == nil {
	  os.Remove(socket)
	}
	lis, err := net.Listen("unix", socket)
  if err != nil {
    log.Fatalf("failed to listen: %v", err)
  }
	fmt.Printf("Listening on %s\n", socket)
	r := &reflector.Reflect{
	    PU_chan: make(chan *reflectorpb.PointUpdate),
		  DB_spec: db_spec}
	go r.TimescaleExportPoint()
  s := grpc.NewServer()
  reflectorpb.RegisterReflectServer(s, r)
  if err := s.Serve(lis); err != nil {
    log.Fatalf("Failed to serve: %v", err)
  }
}
