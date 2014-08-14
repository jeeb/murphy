#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from threading import Thread
from socket import (AF_UNIX, AF_INET, AF_INET6, SOCK_STREAM, SHUT_RDWR)
from struct import (calcsize, pack, unpack)
import asyncore

from mrp_status import Status, StatusQueue

# For basic Py2/Py3 compatibility
try:
    MRP_RANGE = xrange
except NameError:
    MRP_RANGE = range

MRP_DEFAULT_ADDRESS = b"unxs:@murphy-resource-native"
MRP_DEFAULT_RECEIVE_SIZE = 4096
MRP_MSG_TAG_DEFAULT = 0x0

(MRP_MSG_FIELD_INVALID,
 MRP_MSG_FIELD_STRING,
 MRP_MSG_FIELD_INTEGER,
 MRP_MSG_FIELD_UNSIGNED,
 MRP_MSG_FIELD_DOUBLE,
 MRP_MSG_FIELD_BOOL,
 MRP_MSG_FIELD_UINT8,
 MRP_MSG_FIELD_SINT8,
 MRP_MSG_FIELD_UINT16,
 MRP_MSG_FIELD_SINT16,
 MRP_MSG_FIELD_UINT32,
 MRP_MSG_FIELD_SINT32,
 MRP_MSG_FIELD_UINT64,
 MRP_MSG_FIELD_SINT64,
 MRP_MSG_FIELD_BLOB,
 MRP_MSG_FIELD_MAX,
 MRP_MSG_FIELD_ANY,
 MRP_MSG_FIELD_ARRAY) = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c,
                         0x0d, 0x0e, 0x0e, 0x0f, 0x80)

MRP_MSG_FIELD_END = 0x00

(RESPROTO_MESSAGE_END,
 RESPROTO_SECTION_END,
 RESPROTO_ARRAY_DIMENSION,
 RESPROTO_SEQUENCE_NO,
 RESPROTO_REQUEST_TYPE,
 RESPROTO_REQUEST_STATUS,
 RESPROTO_RESOURCE_SET_ID,
 RESPROTO_RESOURCE_STATE,
 RESPROTO_RESOURCE_GRANT,
 RESPROTO_RESOURCE_ADVICE,
 RESPROTO_RESOURCE_ID,
 RESPROTO_RESOURCE_NAME,
 RESPROTO_RESOURCE_FLAGS,
 RESPROTO_RESOURCE_PRIORITY,
 RESPROTO_CLASS_NAME,
 RESPROTO_ZONE_NAME,
 RESPROTO_ATTRIBUTE_INDEX,
 RESPROTO_ATTRIBUTE_NAME,
 RESPROTO_ATTRIBUTE_VALUE) = MRP_RANGE(0x00, 0x13)


def type_to_string(field_type):
    return {
        RESPROTO_MESSAGE_END: "MsgEnd",
        RESPROTO_SECTION_END: "SecEnd",
        RESPROTO_ARRAY_DIMENSION: "ArrDim",
        RESPROTO_SEQUENCE_NO: "SeqNum",
        RESPROTO_REQUEST_TYPE: "ReqType",
        RESPROTO_REQUEST_STATUS: "ReqStatus",
        RESPROTO_RESOURCE_SET_ID: "SetID",
        RESPROTO_RESOURCE_STATE: "ResStatus",
        RESPROTO_RESOURCE_GRANT: "ResGrant",
        RESPROTO_RESOURCE_ADVICE: "ResAdvice",
        RESPROTO_RESOURCE_ID: "ResID",
        RESPROTO_RESOURCE_NAME: "ResName",
        RESPROTO_RESOURCE_FLAGS: "ResFlags",
        RESPROTO_RESOURCE_PRIORITY: "ResPriority",
        RESPROTO_CLASS_NAME: "ClassName",
        RESPROTO_ZONE_NAME: "ZoneName",
        RESPROTO_ATTRIBUTE_INDEX: "AttrIdx",
        RESPROTO_ATTRIBUTE_NAME: "AttrName",
        RESPROTO_ATTRIBUTE_VALUE: "AttrValue",
    }.get(field_type, "Unknown")


def type_to_data_type(field_type):
    return {
        RESPROTO_SECTION_END: (MRP_MSG_FIELD_UINT8, "!B"),
        # RESPROTO_ARRAY_DIMENSION
        RESPROTO_SEQUENCE_NO: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_REQUEST_TYPE: (MRP_MSG_FIELD_UINT16, "!H"),
        RESPROTO_REQUEST_STATUS: (MRP_MSG_FIELD_SINT16, "!h"),
        RESPROTO_RESOURCE_SET_ID: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_RESOURCE_STATE: (MRP_MSG_FIELD_UINT16, "!H"),
        RESPROTO_RESOURCE_GRANT: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_RESOURCE_ADVICE: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_RESOURCE_ID: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_RESOURCE_NAME: (MRP_MSG_FIELD_STRING, "s"),
        RESPROTO_RESOURCE_FLAGS: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_RESOURCE_PRIORITY: (MRP_MSG_FIELD_UINT32, "!L"),
        RESPROTO_CLASS_NAME: (MRP_MSG_FIELD_STRING, "s"),
        RESPROTO_ZONE_NAME: (MRP_MSG_FIELD_STRING, "s"),
        # RESPROTO_ATTRIBUTE_INDEX
        RESPROTO_ATTRIBUTE_NAME: (MRP_MSG_FIELD_STRING, "s"),
        # RESPROTO_ATTRIBUTE_VALUE -> None (default)
    }.get(field_type, None)


(RESPROTO_QUERY_RESOURCES,
 RESPROTO_QUERY_CLASSES,
 RESPROTO_QUERY_ZONES,
 RESPROTO_CREATE_RESOURCE_SET,
 RESPROTO_DESTROY_RESOURCE_SET,
 RESPROTO_ACQUIRE_RESOURCE_SET,
 RESPROTO_RELEASE_RESOURCE_SET,
 RESPROTO_RESOURCES_EVENT) = MRP_RANGE(0x00, 0x08)


def request_type_to_string(query_type):
    return {
        RESPROTO_QUERY_RESOURCES: "Resource Listing",
        RESPROTO_QUERY_CLASSES: "Application Class Listing",
        RESPROTO_QUERY_ZONES: "Application Zone Listing",
        RESPROTO_CREATE_RESOURCE_SET: "Resource Set Creation",
        RESPROTO_DESTROY_RESOURCE_SET: "Resource Set Destruction",
        RESPROTO_ACQUIRE_RESOURCE_SET: "Resource Set Acquisition",
        RESPROTO_RELEASE_RESOURCE_SET: "Resource Set Release",
        RESPROTO_RESOURCES_EVENT: "Resource Event",
    }.get(query_type, "Unknown")


def message_type_to_string(message_type):
    return {
        0: "Default",
    }.get(message_type, "Unknown")


def protocol_to_family(protocol):
    return {
        b"unxs:": AF_UNIX,
        b"tcp4:": AF_INET,
        b"tcp6:": AF_INET6,
    }.get(protocol)


def read_value(data_string, data_type):
    if data_type == "s":
        # With a string, we check the given length and set data type accordingly
        size = len(data_string)
        data_type = "%ss" % (size)
    else:
        # If we're not dealing with a string, we can get the size from struct
        size = calcsize(data_type)

    value = unpack(data_type, data_string[:size])[0]

    # If the read string ends with a null, we remove it
    if (isinstance(value, str) or isinstance(value, bytes)) and value[-1] == b"\0"[0]:
        value = value[:-1]

    return value, size


def write_uint16(value):
    return pack("!H", value)


def write_uint32(value):
    return pack("!L", value)


def write_string(value):
    string = pack("s", value)
    return pack("!L", len(string)) + string


def write_field_value(data_type, value):
    if data_type is not None:
        if data_type[1] == "s":
            # We don't have a trailing null in Python strings, this pads the output with a null byte
            str_len = len(value) + 1
            type_str = "%ss" % (str_len)
        else:
            type_str = data_type[1]

        header = write_uint16(data_type[0])
        string = pack(type_str, value)

        if data_type[0] == MRP_MSG_FIELD_STRING:
            string = write_uint32(len(string)) + string

        string = header + string
    else:
        if isinstance(value, int):
            if value < 0:
                string = write_field_value((MRP_MSG_FIELD_SINT32, "!l"), value)
            else:
                string = write_field_value((MRP_MSG_FIELD_UINT32, "!L"), value)
        elif isinstance(value, float):
            string = write_field_value((MRP_MSG_FIELD_DOUBLE, "d"), value)
        elif isinstance(value, str) or isinstance(value, bytes):
            string = write_field_value((MRP_MSG_FIELD_STRING, "s"), value)
        else:
            print("welp")
            return None

    return string


def write_field(field_type, value):
    string = write_uint16(field_type) + write_field_value(type_to_data_type(field_type), value)

    return string


def read_field_value(data, value_type):
    original_data_length = len(data)

    if value_type == MRP_MSG_FIELD_STRING:
        # We actually read the length first
        length, bytes_read = read_value(data, "!L")
        data = data[bytes_read:]

        # And then we read the actual string
        value, bytes_read = read_value(data[:length], "s")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_BOOL:
        # According to mrp_msg_default_encode uint32 is used for bool
        value, bytes_read = read_value(data, "!L")
        value = bool(value)
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT8:
        value, bytes_read = read_value(data, "!B")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT8:
        value, bytes_read = read_value(data, "!b")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT16:
        value, bytes_read = read_value(data, "!H")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT16:
        value, bytes_read = read_value(data, "!h")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT32:
        value, bytes_read = read_value(data, "!L")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT32:
        value, bytes_read = read_value(data, "!l")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT64:
        value, bytes_read = read_value(data, "!Q")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT64:
        value, bytes_read = read_value(data, "!q")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_DOUBLE:
        value, bytes_read = read_value(data, "d")
        data = data[bytes_read:]
    elif value_type == MRP_MSG_FIELD_BLOB:
        # Read the length first
        length, bytes_read = read_value(data, "!L")
        data = data[bytes_read:]

        value = data[:length]
        data = data[length:]
    elif value_type & MRP_MSG_FIELD_ARRAY:
        value_type &= ~MRP_MSG_FIELD_ARRAY
        counter, bytes_read = read_value(data, "!L")
        data = data[bytes_read:]

        value = []

        for i in MRP_RANGE(counter):
            parsed_value, bytes_read = read_field_value(data, value_type)
            value.append(parsed_value)
            data = data[bytes_read:]
    else:
        print("Unknown type %s found!" % (value_type))
        value = None

    final_length = len(data)

    return value, (original_data_length - final_length)


def read_field(data):
    general_read_amount = 0

    tag, bytes_read = read_value(data, "!H")
    data = data[bytes_read:]

    general_read_amount += bytes_read

    value_type, bytes_read = read_value(data, "!H")
    data = data[bytes_read:]

    general_read_amount += bytes_read

    value, bytes_read = read_field_value(data, value_type)

    general_read_amount += bytes_read

    return Field(tag, value), general_read_amount


def parse_default(data, message):
    # Default message type:
    # [uint16 = number of fields in message]
    #
    # Foreach field:
    # [uint16 = id (0x3, sequence number)]
    # [uint16 = data type (0xn, uint32)]
    # [data (1)]
    # [uint16 = id (0x4, request)]
    # [uint16 = data type (0x10, uint16)]
    # [data (0, resources list)]
    field_count, bytes_read = read_value(data, "!H")
    data = data[bytes_read:]
    print("Field count in message: %s" % (field_count))

    for i in MRP_RANGE(field_count):
        field, bytes_read = read_field(data)
        data = data[bytes_read:]

        if field.type is RESPROTO_SEQUENCE_NO:
            message.seq_num = field.value
        elif field.type is RESPROTO_REQUEST_TYPE:
            message.req_type = field.value

        message.add_field(field)

    return message


def parse_message(data):
    # Message header:
    # [uint16 = data type tag (0x0 = default)]
    message = MurphyMessage()

    # Message type
    message.type, bytes_read = read_value(data, "!H")
    data = data[bytes_read:]

    if message.type == MRP_MSG_TAG_DEFAULT:
        parse_default(data, message)
    else:
        print("Unknown message type %s" % (message.type))
        return None

    return message


class MurphyMessage(object):
    def __init__(self):
        self.__msg_type = -1
        self.__req_type = -1
        self.__seq_num = -1
        self._msg_fields = []

    @property
    def type(self):
        return self.__msg_type

    @type.setter
    def type(self, val):
        self.__msg_type = val

    @property
    def fields(self):
        return self._msg_fields

    def add_field(self, val):
        self._msg_fields.append(val)

    @property
    def seq_num(self):
        return self.__seq_num

    @seq_num.setter
    def seq_num(self, val):
        self.__seq_num = val

    @property
    def req_type(self):
        return self.__req_type

    @req_type.setter
    def req_type(self, val):
        self.__req_type = val

    def convert_to_byte_stream(self):
        pass

    def pretty_print(self):
        string = "Message:\n"\
                 "\tType: %s (%d)\n\n" % (message_type_to_string(self.type), self.type)

        for field in self.fields:
            if field.type == RESPROTO_REQUEST_TYPE:
                string += "\tField: %s (%d) | %s (%s)\n" % (type_to_string(field.type), field.type,
                                                            request_type_to_string(field.value), field.value)
            else:
                string += "\tField: %s (%d) | %s\n" % (type_to_string(field.type), field.type, field.value)

        return string


class Field(object):
    def __init__(self, field_type, field_value):
        self.__field_type = field_type
        self.__field_value = field_value

    @property
    def type(self):
        return self.__field_type

    @property
    def value(self):
        return self.__field_value


class MurphyConnection(asyncore.dispatcher_with_send):
    def __init__(self, address, daemonize=True):
        asyncore.dispatcher_with_send.__init__(self)

        family = protocol_to_family(address[:5])
        if not family:
            raise ValueError("Unknown protocol %s!" % (address[:5]))

        address = address[5:]

        if family is AF_UNIX and address[0] == b"@"[0]:
            address = b"\0" + address[1:]

        self.create_socket(family, SOCK_STREAM)
        self.connect(address)

        self.family = family
        self.address = address
        self._internal_counter = 1

        self.events = []
        self.queue = StatusQueue()
        self.own_sets = dict()

        self.thread = Thread(target=asyncore.loop)
        self.thread.daemon = daemonize
        self.thread.start()

    def close(self):
        self.socket.shutdown(SHUT_RDWR)
        asyncore.dispatcher_with_send.close(self)

    def read_message(self, read_buffer):
        header_size = calcsize("!L")
        full_size = len(read_buffer)

        # If we don't have the size header amount of data,
        # we try to get data until we have the needed amount
        while len(read_buffer) < header_size:
            read_buffer += self.recv(MRP_DEFAULT_RECEIVE_SIZE)

        # Now we should have at least enough to read the size
        message_size = unpack("!L", read_buffer[:header_size])[0]
        read_buffer = read_buffer[header_size:]

        print("Full size %s = %s + %s" % (full_size, message_size, header_size))

        # Read until we have the full message
        while len(read_buffer) < message_size:
            read_buffer += self.recv(MRP_DEFAULT_RECEIVE_SIZE)

        return read_buffer, message_size

    def check_message(self, message):
        queue = self.queue.contents

        if message.seq_num in queue:
            if message.req_type in queue.get(message.seq_num):
                print("D: Got a response to a sent message! (seq %s - type %s)" % (message.seq_num, message.req_type))
                queue.get(message.seq_num, {}).get(message.req_type).set_result(message)
                return

    def handle_read(self):
        # Do an initial read
        read_buffer = self.recv(MRP_DEFAULT_RECEIVE_SIZE)

        while len(read_buffer) > 0:
            read_buffer, message_size = self.read_message(read_buffer)
            message = parse_message(read_buffer)
            self.check_message(message)
            print(message.pretty_print())
            read_buffer = read_buffer[message_size:]
            print("Reader length: %s" % (len(read_buffer)))

    def send_message(self, msg_buffer):
        amount_to_write = len(msg_buffer)

        self.send(pack("!L", amount_to_write) + msg_buffer)

    def give_seq_and_increment(self):
        """
        Returns the current value of the internal counter for sequence IDs, and
        increments it by one.

        :return: Integer value representing the current value of the internal
                 counter for sequence IDs
        """
        current = self._internal_counter
        self._internal_counter += 1
        return current

    def write_sequence_number(self):
        return write_field(RESPROTO_SEQUENCE_NO, self.give_seq_and_increment())

    def create_request(self, value):
        byte_stream = write_uint16(MRP_MSG_TAG_DEFAULT)
        byte_stream += write_uint16(2)
        byte_stream += self.write_sequence_number()
        byte_stream += write_field(RESPROTO_REQUEST_TYPE, value)

        return byte_stream

    def send_request(self, request_type):
        status = Status()
        byte_stream = self.create_request(request_type)

        message = parse_message(byte_stream)

        self.queue.add(message.req_type, message.seq_num, status)

        self.send_message(byte_stream)

        gatekeeper = status.wait(5.0)
        self.queue.remove(message.req_type, message.seq_num)

        # If gatekeeper tells us that we didn't get a response, we timed out
        if not gatekeeper:
            print("E: Timed out on the response (waited five seconds; seq %s - type %s)" % (message.seq_num,
                                                                                            message.req_type))
            return None

        # Get the response data from the status object
        response = status.get_result()

        # Delete the status object itself
        del(status)

        return response

    def list_resources(self):
        return self.send_request(RESPROTO_QUERY_RESOURCES)

    def list_classes(self):
        return self.send_request(RESPROTO_QUERY_CLASSES)

    def list_zones(self):
        return self.send_request(RESPROTO_QUERY_ZONES)

    def create_set(self, resources=None):
        status = Status()
        status2 = Status()

        byte_stream = write_uint16(MRP_MSG_TAG_DEFAULT)

        # Field count
        byte_stream += write_uint16(14)

        byte_stream += self.write_sequence_number()
        byte_stream += write_field(RESPROTO_REQUEST_TYPE, RESPROTO_CREATE_RESOURCE_SET)
        byte_stream += write_field(RESPROTO_RESOURCE_FLAGS, 0)
        byte_stream += write_field(RESPROTO_RESOURCE_PRIORITY, 0)
        byte_stream += write_field(RESPROTO_CLASS_NAME, b"player")
        byte_stream += write_field(RESPROTO_ZONE_NAME, b"driver")
        byte_stream += write_field(RESPROTO_RESOURCE_NAME, b"audio_playback")
        byte_stream += write_field(RESPROTO_RESOURCE_FLAGS, 3)
        byte_stream += write_field(RESPROTO_ATTRIBUTE_NAME, b"role")
        byte_stream += write_field(RESPROTO_ATTRIBUTE_VALUE, b"video")
        byte_stream += write_field(RESPROTO_SECTION_END, MRP_MSG_TAG_DEFAULT)
        byte_stream += write_field(RESPROTO_RESOURCE_NAME, b"video_playback")
        byte_stream += write_field(RESPROTO_RESOURCE_FLAGS, 1)
        byte_stream += write_field(RESPROTO_SECTION_END, MRP_MSG_TAG_DEFAULT)

        message = parse_message(byte_stream)
        print(message.pretty_print())

        self.queue.add(RESPROTO_RESOURCES_EVENT, message.seq_num, status)
        self.queue.add(message.req_type, message.seq_num, status2)

        self.send_message(byte_stream)

        gatekeeper = status.wait(5.0)
        gatekeeper = status2.wait(5.0)

        self.queue.remove(RESPROTO_RESOURCES_EVENT, message.seq_num)
        self.queue.remove(message.req_type, message.seq_num)

        # If gatekeeper tells us that we didn't get a response, we timed out
        if not gatekeeper:
            print("E: Timed out on the response (waited five seconds; seq %s - type %s)" % (message.seq_num,
                                                                                            message.req_type))
            return None

        # Get the response data from the status object
        response = status.get_result()

        # Delete the status object itself
        del(status)

        return response
