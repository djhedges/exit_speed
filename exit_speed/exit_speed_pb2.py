# pytype: skip-file
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: exit_speed.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='exit_speed.proto',
  package='exit_speed',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x10\x65xit_speed.proto\x12\nexit_speed\x1a\x1fgoogle/protobuf/timestamp.proto\"h\n\x03Gps\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0b\n\x03lat\x18\x02 \x01(\x01\x12\x0b\n\x03lon\x18\x03 \x01(\x01\x12\x0b\n\x03\x61lt\x18\x04 \x01(\x01\x12\x10\n\x08speed_ms\x18\x05 \x01(\x01\"\x84\x01\n\rAccelerometer\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x17\n\x0f\x61\x63\x63\x65lerometer_x\x18\x02 \x01(\x01\x12\x17\n\x0f\x61\x63\x63\x65lerometer_y\x18\x03 \x01(\x01\x12\x17\n\x0f\x61\x63\x63\x65lerometer_z\x18\x04 \x01(\x01\"e\n\tGyroscope\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0e\n\x06gyro_x\x18\x02 \x01(\x01\x12\x0e\n\x06gyro_y\x18\x03 \x01(\x01\x12\x0e\n\x06gyro_z\x18\x04 \x01(\x01\"\xd3\x02\n\x07Labjack\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x16\n\x0elabjack_temp_f\x18\x02 \x01(\x01\x12\x1a\n\x12\x66uel_level_voltage\x18\x03 \x01(\x01\x12\x13\n\x0btps_voltage\x18\x04 \x01(\x01\x12\x1a\n\x12water_temp_voltage\x18\x05 \x01(\x01\x12\x1c\n\x14oil_pressure_voltage\x18\x06 \x01(\x01\x12$\n\x1c\x66ront_brake_pressure_voltage\x18\x07 \x01(\x01\x12#\n\x1brear_brake_pressure_voltage\x18\x08 \x01(\x01\x12\x17\n\x0f\x62\x61ttery_voltage\x18\t \x01(\x01\x12\x18\n\x10oil_temp_voltage\x18\n \x01(\x01\x12\x1d\n\x15\x66uel_pressure_voltage\x18\x0b \x01(\x01\"J\n\x04WBO2\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0b\n\x03rpm\x18\x02 \x01(\x01\x12\x0b\n\x03\x61\x66r\x18\x03 \x01(\x01\"\xcf\x01\n\rTireIrSensors\x12.\n\x0clf_tire_temp\x18\x01 \x01(\x0b\x32\x18.exit_speed.TireIrSensor\x12.\n\x0crf_tire_temp\x18\x02 \x01(\x0b\x32\x18.exit_speed.TireIrSensor\x12.\n\x0clr_tire_temp\x18\x03 \x01(\x0b\x32\x18.exit_speed.TireIrSensor\x12.\n\x0crr_tire_temp\x18\x04 \x01(\x0b\x32\x18.exit_speed.TireIrSensor\"f\n\x0cTireIrSensor\x12(\n\x04time\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\r\n\x05inner\x18\x02 \x01(\x01\x12\x0e\n\x06middle\x18\x03 \x01(\x01\x12\r\n\x05outer\x18\x04 \x01(\x01\x62\x06proto3')
  ,
  dependencies=[google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR,])




_GPS = _descriptor.Descriptor(
  name='Gps',
  full_name='exit_speed.Gps',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.Gps.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lat', full_name='exit_speed.Gps.lat', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lon', full_name='exit_speed.Gps.lon', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='alt', full_name='exit_speed.Gps.alt', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='speed_ms', full_name='exit_speed.Gps.speed_ms', index=4,
      number=5, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=65,
  serialized_end=169,
)


_ACCELEROMETER = _descriptor.Descriptor(
  name='Accelerometer',
  full_name='exit_speed.Accelerometer',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.Accelerometer.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='accelerometer_x', full_name='exit_speed.Accelerometer.accelerometer_x', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='accelerometer_y', full_name='exit_speed.Accelerometer.accelerometer_y', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='accelerometer_z', full_name='exit_speed.Accelerometer.accelerometer_z', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=172,
  serialized_end=304,
)


_GYROSCOPE = _descriptor.Descriptor(
  name='Gyroscope',
  full_name='exit_speed.Gyroscope',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.Gyroscope.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gyro_x', full_name='exit_speed.Gyroscope.gyro_x', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gyro_y', full_name='exit_speed.Gyroscope.gyro_y', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gyro_z', full_name='exit_speed.Gyroscope.gyro_z', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=306,
  serialized_end=407,
)


_LABJACK = _descriptor.Descriptor(
  name='Labjack',
  full_name='exit_speed.Labjack',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.Labjack.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='labjack_temp_f', full_name='exit_speed.Labjack.labjack_temp_f', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fuel_level_voltage', full_name='exit_speed.Labjack.fuel_level_voltage', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='tps_voltage', full_name='exit_speed.Labjack.tps_voltage', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='water_temp_voltage', full_name='exit_speed.Labjack.water_temp_voltage', index=4,
      number=5, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='oil_pressure_voltage', full_name='exit_speed.Labjack.oil_pressure_voltage', index=5,
      number=6, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='front_brake_pressure_voltage', full_name='exit_speed.Labjack.front_brake_pressure_voltage', index=6,
      number=7, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rear_brake_pressure_voltage', full_name='exit_speed.Labjack.rear_brake_pressure_voltage', index=7,
      number=8, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='battery_voltage', full_name='exit_speed.Labjack.battery_voltage', index=8,
      number=9, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='oil_temp_voltage', full_name='exit_speed.Labjack.oil_temp_voltage', index=9,
      number=10, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='fuel_pressure_voltage', full_name='exit_speed.Labjack.fuel_pressure_voltage', index=10,
      number=11, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=410,
  serialized_end=749,
)


_WBO2 = _descriptor.Descriptor(
  name='WBO2',
  full_name='exit_speed.WBO2',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.WBO2.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rpm', full_name='exit_speed.WBO2.rpm', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='afr', full_name='exit_speed.WBO2.afr', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=751,
  serialized_end=825,
)


_TIREIRSENSORS = _descriptor.Descriptor(
  name='TireIrSensors',
  full_name='exit_speed.TireIrSensors',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='lf_tire_temp', full_name='exit_speed.TireIrSensors.lf_tire_temp', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rf_tire_temp', full_name='exit_speed.TireIrSensors.rf_tire_temp', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lr_tire_temp', full_name='exit_speed.TireIrSensors.lr_tire_temp', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rr_tire_temp', full_name='exit_speed.TireIrSensors.rr_tire_temp', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=828,
  serialized_end=1035,
)


_TIREIRSENSOR = _descriptor.Descriptor(
  name='TireIrSensor',
  full_name='exit_speed.TireIrSensor',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='exit_speed.TireIrSensor.time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='inner', full_name='exit_speed.TireIrSensor.inner', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='middle', full_name='exit_speed.TireIrSensor.middle', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='outer', full_name='exit_speed.TireIrSensor.outer', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1037,
  serialized_end=1139,
)

_GPS.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
_ACCELEROMETER.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
_GYROSCOPE.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
_LABJACK.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
_WBO2.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
_TIREIRSENSORS.fields_by_name['lf_tire_temp'].message_type = _TIREIRSENSOR
_TIREIRSENSORS.fields_by_name['rf_tire_temp'].message_type = _TIREIRSENSOR
_TIREIRSENSORS.fields_by_name['lr_tire_temp'].message_type = _TIREIRSENSOR
_TIREIRSENSORS.fields_by_name['rr_tire_temp'].message_type = _TIREIRSENSOR
_TIREIRSENSOR.fields_by_name['time'].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
DESCRIPTOR.message_types_by_name['Gps'] = _GPS
DESCRIPTOR.message_types_by_name['Accelerometer'] = _ACCELEROMETER
DESCRIPTOR.message_types_by_name['Gyroscope'] = _GYROSCOPE
DESCRIPTOR.message_types_by_name['Labjack'] = _LABJACK
DESCRIPTOR.message_types_by_name['WBO2'] = _WBO2
DESCRIPTOR.message_types_by_name['TireIrSensors'] = _TIREIRSENSORS
DESCRIPTOR.message_types_by_name['TireIrSensor'] = _TIREIRSENSOR
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Gps = _reflection.GeneratedProtocolMessageType('Gps', (_message.Message,), dict(
  DESCRIPTOR = _GPS,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.Gps)
  ))
_sym_db.RegisterMessage(Gps)

Accelerometer = _reflection.GeneratedProtocolMessageType('Accelerometer', (_message.Message,), dict(
  DESCRIPTOR = _ACCELEROMETER,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.Accelerometer)
  ))
_sym_db.RegisterMessage(Accelerometer)

Gyroscope = _reflection.GeneratedProtocolMessageType('Gyroscope', (_message.Message,), dict(
  DESCRIPTOR = _GYROSCOPE,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.Gyroscope)
  ))
_sym_db.RegisterMessage(Gyroscope)

Labjack = _reflection.GeneratedProtocolMessageType('Labjack', (_message.Message,), dict(
  DESCRIPTOR = _LABJACK,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.Labjack)
  ))
_sym_db.RegisterMessage(Labjack)

WBO2 = _reflection.GeneratedProtocolMessageType('WBO2', (_message.Message,), dict(
  DESCRIPTOR = _WBO2,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.WBO2)
  ))
_sym_db.RegisterMessage(WBO2)

TireIrSensors = _reflection.GeneratedProtocolMessageType('TireIrSensors', (_message.Message,), dict(
  DESCRIPTOR = _TIREIRSENSORS,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.TireIrSensors)
  ))
_sym_db.RegisterMessage(TireIrSensors)

TireIrSensor = _reflection.GeneratedProtocolMessageType('TireIrSensor', (_message.Message,), dict(
  DESCRIPTOR = _TIREIRSENSOR,
  __module__ = 'exit_speed_pb2'
  # @@protoc_insertion_point(class_scope:exit_speed.TireIrSensor)
  ))
_sym_db.RegisterMessage(TireIrSensor)


# @@protoc_insertion_point(module_scope)