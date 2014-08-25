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
MRP_DEFAULT_TIMEOUT = 5.0
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


def data_type_to_string(data_type):
    """
    Returns the string representation of a field data type

    :param data_type: Integer that represents a field's data type
    :return:          String representation of the given field data type
    """
    return {
        MRP_MSG_FIELD_INVALID: "Invalid",
        MRP_MSG_FIELD_STRING: "String",
        MRP_MSG_FIELD_INTEGER: "Int",
        MRP_MSG_FIELD_UNSIGNED: "UInt",
        MRP_MSG_FIELD_DOUBLE: "Double",
        MRP_MSG_FIELD_BOOL: "Bool",
        MRP_MSG_FIELD_UINT8: "UInt8",
        MRP_MSG_FIELD_SINT8: "SInt8",
        MRP_MSG_FIELD_UINT16: "UInt16",
        MRP_MSG_FIELD_SINT16: "SInt16",
        MRP_MSG_FIELD_UINT32: "UInt32",
        MRP_MSG_FIELD_SINT32: "SInt32",
        MRP_MSG_FIELD_UINT64: "UInt64",
        MRP_MSG_FIELD_SINT64: "SInt64",
        MRP_MSG_FIELD_BLOB: "Blob",
        MRP_MSG_FIELD_ANY: "Any",
        MRP_MSG_FIELD_ARRAY: "Array",
    }.get(data_type, "Unknown")


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
    """
    Returns the string representation of a field type

    :param field_type: Integer that represents a field's type
    :return:           String representation of the given field type
    """
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
    """
    Returns the field data type and struct format string based on a field type

    :param field_type: Integer that represents a field's type
    :return:           None if the value is not defined, otherwise a Tuple that
                       contains the integer representation of the field data type
                       as well as the format string for this field data type

    """
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
    """
    Returns the string representation of a protocol request type

    :param query_type: Integer that represents a protocol request type
    :return:           "Unknown" if value is not defined, String representation of the
                       protocol request type otherwise
    """
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
    """
    Returns the string representation of a protocol message type

    :param message_type: Integer that represents a protocol message type
    :return:             "Unknown" if value is not defined, String representation of the
                         protocol message type otherwise
    """
    return {
        0: "Default",
    }.get(message_type, "Unknown")


def protocol_to_family(protocol):
    """
    Returns the socket protocol value of a given protocol type

    :param protocol: String that represents a protocol type
    :return:         None if no protocol matched, a socket type value otherwise
    """
    return {
        b"unxs:": AF_UNIX,
        b"tcp4:": AF_INET,
        b"tcp6:": AF_INET6,
    }.get(protocol)


def read_value(byte_string, format_string):
    """
    Reads a value from a byte string based upon its format string

    :param byte_string:   Byte string from which the value will be read. Has to be exactly
                          as long as needed, or longer. Strings are read by their length, so
                          they have to be exactly as long as marked
    :param format_string: String that represents the data type to be read from the byte string.
                          When reading a string, no length is needed, "s" is enough
    :return:              Tuple that contains the read value as well as the the amount of byte
                          string that was read
    """
    if format_string == "s":
        # With a string, we check the given length and set data type accordingly
        size = len(byte_string)
        format_string = "%ss" % (size)
    else:
        # If we're not dealing with a string, we can get the size from struct
        size = calcsize(format_string)

    value = unpack(format_string, byte_string[:size])[0]

    # If the read string ends with a null, we remove it
    if (isinstance(value, str) or isinstance(value, bytes)) and value[-1] == b"\0"[0]:
        value = value[:-1]

    return value, size


def write_uint16(value):
    """
    Writes a byte string that contains a given uint16 value

    :param value: Integer that is to be written out as a byte string
    :return:      Byte string that contains the given uint16 value
    """
    return pack("!H", value)


def write_uint32(value):
    """
    Writes a byte string that contains a given uint32 value

    :param value: Integer that is to be written out as a byte string
    :return:      Byte string that contains the given uint32 value
    """
    return pack("!L", value)


def write_string(value):
    """
    Writes a byte string that contains a length-prefixed string as
    sent/received by the protocol

    :param value: String that is to be written out as a byte string
    :return:      Byte string that contains the given string length-prefixed
    """
    string = pack("s", value)
    return pack("!L", len(string)) + string


def write_field_value(data_type, value):
    """
    Writes the value part of a field to a byte string. this includes
    the value data type as well as the value itself

    :param data_type: Tuple that contains the integer representation of the field data type
                      as well as the format string for this field data type, such as returned by
                      type_to_data_type
    :param value:     Actual value to be written
    :return:          None if an error occurred, a byte string with a field's value part in it
                      otherwise
    """
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
    """
    Writes a field to a byte string (field type, field's data type and the field's value itself)

    :param field_type: Type of field to be written
    :param value:      Value to be written into the field
    :return:           Byte string that contains the field
    """
    string = write_uint16(field_type) + write_field_value(type_to_data_type(field_type), value)

    return string


def read_field_value(byte_string, value_type):
    """
    Reads a field's value out of a byte string

    :param byte_string: Byte string to read a value from
    :param value_type:  Integer representation (MRP_MSG_FIELD_*) of the type of value
                        to be read
    :return:            Tuple that contains the value read (or None if failure occurred),
                        and the amount of byte string that was read
    """
    original_data_length = len(byte_string)

    if value_type == MRP_MSG_FIELD_STRING:
        # We actually read the length first
        length, bytes_read = read_value(byte_string, "!L")
        byte_string = byte_string[bytes_read:]

        # And then we read the actual string
        value, bytes_read = read_value(byte_string[:length], "s")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_BOOL:
        # According to mrp_msg_default_encode uint32 is used for bool
        value, bytes_read = read_value(byte_string, "!L")
        value = bool(value)
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT8:
        value, bytes_read = read_value(byte_string, "!B")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT8:
        value, bytes_read = read_value(byte_string, "!b")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT16:
        value, bytes_read = read_value(byte_string, "!H")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT16:
        value, bytes_read = read_value(byte_string, "!h")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT32:
        value, bytes_read = read_value(byte_string, "!L")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT32:
        value, bytes_read = read_value(byte_string, "!l")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_UINT64:
        value, bytes_read = read_value(byte_string, "!Q")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_SINT64:
        value, bytes_read = read_value(byte_string, "!q")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_DOUBLE:
        value, bytes_read = read_value(byte_string, "d")
        byte_string = byte_string[bytes_read:]
    elif value_type == MRP_MSG_FIELD_BLOB:
        # Read the length first
        length, bytes_read = read_value(byte_string, "!L")
        byte_string = byte_string[bytes_read:]

        value = byte_string[:length]
        byte_string = byte_string[length:]
    elif value_type & MRP_MSG_FIELD_ARRAY:
        value_type &= ~MRP_MSG_FIELD_ARRAY
        counter, bytes_read = read_value(byte_string, "!L")
        byte_string = byte_string[bytes_read:]

        value = []

        for _ in MRP_RANGE(counter):
            parsed_value, bytes_read = read_field_value(byte_string, value_type)
            value.append(parsed_value)
            byte_string = byte_string[bytes_read:]
    else:
        print("Unknown type %s found!" % (value_type))
        value = None

    final_length = len(byte_string)

    return value, (original_data_length - final_length)


def read_field(byte_string):
    """
    Reads a single field out of a byte string

    :param byte_string: Byte string to read the field from
    :return:            Tuple that contains a Field object as well as
                        the amount of byte string that was read
    """
    general_read_amount = 0

    tag, bytes_read = read_value(byte_string, "!H")
    byte_string = byte_string[bytes_read:]

    general_read_amount += bytes_read

    value_type, bytes_read = read_value(byte_string, "!H")
    byte_string = byte_string[bytes_read:]

    general_read_amount += bytes_read

    value, bytes_read = read_field_value(byte_string, value_type)

    general_read_amount += bytes_read

    return Field(tag, value_type, value), general_read_amount


def parse_default(byte_string):
    """
    Parses an MRP_MSG_TAG_DEFAULT (default message type) structure from
    a byte string

    Structure:
        [uint16 = number of fields in message]

        foreach field:
            [uint16 = field type]
            [uint16 = field data type]
            [variable length data (depends on type)]

    :param byte_string: Byte string to parse the message from
    :return:            DefaultMessage containing the parsed information
    """
    message = DefaultMessage()

    field_count, bytes_read = read_value(byte_string, "!H")
    byte_string = byte_string[bytes_read:]
    print("Field count in message: %s" % (field_count))

    for _ in MRP_RANGE(field_count):
        field, bytes_read = read_field(byte_string)
        byte_string = byte_string[bytes_read:]

        message.add_field_obj(field)

    return message


def parse_message(byte_string):
    """
    Parses a Murphy resource protocol message delivered via a byte string to
    a MurphyMessage instance

    :param byte_string: Byte string to parse
    :return:            None in case of failure, MurphyMessage instance with the
                        parsed fields otherwise
    """
    # Message type [uint16 = message type (0x0 = default)]
    msg_type, bytes_read = read_value(byte_string, "!H")
    byte_string = byte_string[bytes_read:]

    if msg_type == MRP_MSG_TAG_DEFAULT:
        message = parse_default(byte_string)
    else:
        print("Unknown message type %s" % (msg_type))
        return None

    return message


def parse_message_to_resource_set(message, given_res_set=None):
    """
    Parses a ResourceSet out of a MurphyMessage instance

    :param message:       MurphyMessage instance to parse the information from
    :param given_res_set: Possible already existing ResourceSet instance to update
    :return:              Newly created or updated ResourceSet instance
    """
    res_set = ResourceSet()
    res = Resource()
    grant = None
    advice = None
    cached_value = None

    # We make a copy of the original list as we will be removing fields
    fields = list(message.fields)

    # Parse resource set information
    for field in list(fields):
        if field.type is RESPROTO_RESOURCE_ID or field.type is RESPROTO_RESOURCE_NAME:
            # We move to parsing the per-resource information
            break
        else:
            if field.type is RESPROTO_RESOURCE_SET_ID:
                res_set.id = field.value
                fields.remove(field)

            elif field.type is RESPROTO_RESOURCE_STATE:
                res_set.acquired = bool(field.value)
                fields.remove(field)

            elif field.type is RESPROTO_RESOURCE_GRANT:
                grant = field.value
                fields.remove(field)

            elif field.type is RESPROTO_RESOURCE_ADVICE:
                advice = field.value
                fields.remove(field)

            elif field.type is RESPROTO_RESOURCE_FLAGS:
                res_set.autorelease = bool(field.value & 1)
                res_set.autoacquire = bool(field.value & 2)
                res_set.no_events = bool(field.value & 4)
                res_set.dont_wait = bool(field.value & 8)
                fields.remove(field)

            elif field.type is RESPROTO_RESOURCE_PRIORITY:
                res_set.priority = field.value

    # Now parse the per-resource information
    for field in fields:
        if field.type is RESPROTO_RESOURCE_ID:
            res.id = field.value
            res.acquired = bool(grant & 1 << field.value)
            res.available = bool(advice & 1 << field.value)

        elif field.type is RESPROTO_RESOURCE_NAME:
            res.name = field.value

        elif field.type is RESPROTO_RESOURCE_FLAGS:
            res.mandatory = bool(field.value & 1)
            res.shareable = bool(field.value & 2)

        elif field.type is RESPROTO_ATTRIBUTE_NAME:
            cached_value = field.value

        elif field.type is RESPROTO_ATTRIBUTE_VALUE:
            if cached_value is None:
                ValueError("Parser error: Attribute value without name!?")

            res.add_attribute(Attribute(cached_value, field.data_type, field.value))
            cached_value = None

        elif field.type is RESPROTO_SECTION_END:
            # A single resource's information has ended, we commit
            res_set.add_resource(res)
            res = Resource()
            cached_value = None

    # Now, if we have had a set given to us, update it
    if given_res_set:
        given_res_set.update(res_set.data)

        for res in given_res_set.resources.values():
            updated_res = res_set.resources.get(res.name)

            # If the resource is available in the update, update it
            if updated_res is not None:
                print("D: Updating res %s" % (updated_res.name))
                res.update(updated_res.data)
                res.attributes.update(updated_res.attributes)
            elif res.id is not None:
                print("D: Res %s not transferred, using grant/advice" % (res.name))
                res.acquired = bool(grant & 1 << res.id)
                res.available = bool(advice & 1 << res.id)
            else:
                print("D: Res %s not transferred and doesn't yet have an ID - implicit values used" % (res.name))

        # And actually return the updated one
        res_set = given_res_set

    return res_set


class MurphyMessage(object):
    def __init__(self):
        """
        Abstraction of the fields transferred in a Murphy resource protocol
        """
        self.__msg_type = -1
        self._msg_fields = []

    @property
    def type(self):
        """
        Murphy resource protocol message type

        :return: Integer representing the set message type
        """
        return self.__msg_type

    @type.setter
    def type(self, val):
        self.__msg_type = val

    @property
    def fields(self):
        """
        List of fields contained within this message

        :return: List of Fields contained in this Murphy resource protocol message
        """
        return self._msg_fields

    def add_field(self, field_type, field_value):
        """
        Adds a Field to the list of fields based on its information

        :param field_type:  Integer representing the field type
        :param field_value: Value the be set to this field
        :return:            Void
        """
        field = Field(field_type, type_to_data_type(field_type)[0], field_value)
        self.fields.append(field)

    def add_field_obj(self, obj):
        """
        Adds a Field object to the list of fields

        :param obj: Field instance to append to the list of fields
        :return:    Void
        """
        self.fields.append(obj)

    def add_attribute(self, attr_name, attr_type, attr_value):
        """
        Adds a Field-based representation of a resource attribute to the list of fields

        :param attr_name:  Name of attribute to be added
        :param attr_type:  Data type of attribute to be added
        :param attr_value: Value of attribute to be added
        :return:           Void
        """
        self.add_field_obj(Field(RESPROTO_ATTRIBUTE_NAME, MRP_MSG_FIELD_STRING, attr_name))
        self.add_field_obj(Field(RESPROTO_ATTRIBUTE_VALUE, attr_type, attr_value))

    def add_resource(self, resource):
        """
        Adds a Field-based representation of a resource to the list of fields

        :param resource: Resource instance to be added
        :return:         Void
        """
        res_flags = 0

        self.add_field(RESPROTO_RESOURCE_NAME, resource.name)

        if resource.mandatory:
            res_flags += 1

        if resource.shareable:
            res_flags += 2

        self.add_field(RESPROTO_RESOURCE_FLAGS, res_flags)

        for attr in resource.attributes.values():
            self.add_attribute(attr.name, attr.data_type, attr.value)

        self.add_field(RESPROTO_SECTION_END, MRP_MSG_TAG_DEFAULT)

    def add_resources(self, resources):
        """
        Adds a Field-based representation of multiple resources to the list of fields

        :param resources: List of Resource instances to be added
        :return:          Void
        """
        for resource in resources:
            self.add_resource(resource)

    @property
    def seq_num(self):
        """
        Sequence number of this message, is the first field

        :return: None if not yet set, integer with the sequence number otherwise
        :raises: ValueError if there are fields, but the first one isn't a sequence number
        """
        if self.fields:
            field = self.fields[0]
            if field.type is not RESPROTO_SEQUENCE_NO:
                raise ValueError("We have fields, but the sequence number is not the first one!")
            else:
                return field.value
        else:
            # The sequence number is not yet set
            return None

    @seq_num.setter
    def seq_num(self, val):
        if self.seq_num:
            field = self.fields[0]
            field.value = val
        else:
            self.add_field(RESPROTO_SEQUENCE_NO, val)

    @property
    def req_type(self):
        """
        Request type contained within this message

        :return: None if a request type is not contained within this message,
                 integer representing the request type otherwise
        """
        for field in self.fields:
            if field.type == RESPROTO_REQUEST_TYPE:
                return field.value

        # We didn't have the request type available
        return None

    @property
    def length(self):
        """
        Count of fields in this message

        :return: Integer representing the amount of fields in this message
        """
        return len(self._msg_fields)

    def pretty_print(self):
        """
        Returns a human-readable representation of this MurphyMessage instance

        :return: String containing the human-readable representation of this
                 MurphyMessage instance
        """
        string = "Message:\n"\
                 "\tType: %s (%d)\n\n" % (message_type_to_string(self.type), self.type)

        for field in self.fields:
            if field.type == RESPROTO_REQUEST_TYPE:
                string += "\tField: %s (%d) = <%s> %s (%s)\n" % (type_to_string(field.type), field.type,
                                                                 data_type_to_string(field.data_type),
                                                                 request_type_to_string(field.value),
                                                                 field.value)
            else:
                string += "\tField: %s (%d) = <%s> %s\n" % (type_to_string(field.type), field.type,
                                                            data_type_to_string(field.data_type),
                                                            field.value)

        return string


class DefaultMessage(MurphyMessage):
    def __init__(self, seq_num=None):
        """
        Abstraction of a Murphy resource protocol message of the type
        MRP_MSG_TAG_DEFAULT

        :param seq_num: Optional, sequence number of this message
        """
        super(DefaultMessage, self).__init__()
        self.type = MRP_MSG_TAG_DEFAULT

        if seq_num is not None:
            self.seq_num = seq_num

    def convert_to_byte_string(self):
        """
        Creates a byte string representation of this message

        :return: Byte string representation of this message
        """
        byte_stream = write_uint16(self.type)
        byte_stream += write_uint16(self.length)

        for field in self.fields:
            byte_stream += write_field(field.type, field.value)

        return byte_stream


class ApplicationClassListing(DefaultMessage):
    def __init__(self, seq_num):
        """
        Abstraction of a Murphy resource protocol message containing an
        application class listing request

        :param seq_num: Sequence number of this message
        """
        super(ApplicationClassListing, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_QUERY_CLASSES)


class ZoneListing(DefaultMessage):
    def __init__(self, seq_num):
        """
        Abstraction of a Murphy resource protocol message containing a
        zone listing request

        :param seq_num: Sequence number of this message
        """
        super(ZoneListing, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_QUERY_ZONES)


class ResourceListing(DefaultMessage):
    def __init__(self, seq_num):
        """
        Abstraction of a Murphy resource protocol message containing a
        resource listing request

        :param seq_num: Sequence number of this message
        """
        super(ResourceListing, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_QUERY_RESOURCES)


class ResourceSetCreation(DefaultMessage):
    def __init__(self, seq_num, res_set, app_class, zone):
        """
        Abstraction of a Murphy resource protocol message containing a
        resource set creation request

        :param seq_num:   Sequence number of this message
        :param res_set:   ResourceSet object containing the requested resources
                          as well as the set's flags
        :param app_class: Application class the created set will be part of
        :param zone:      Zone the created set will be part of
        """
        super(ResourceSetCreation, self).__init__(seq_num)
        flags = 0

        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_CREATE_RESOURCE_SET)

        if res_set.autorelease:
            flags += 1

        if res_set.autoacquire:
            flags += 2

        if res_set.no_events:
            flags += 4

        if res_set.dont_wait:
            flags += 8

        self.add_field(RESPROTO_RESOURCE_FLAGS, flags)
        self.add_field(RESPROTO_RESOURCE_PRIORITY, res_set.priority)
        self.add_field(RESPROTO_CLASS_NAME, app_class)
        self.add_field(RESPROTO_ZONE_NAME, zone)

        self.add_resources(res_set.resources.values())


class ResourceSetDestruction(DefaultMessage):
    def __init__(self, seq_num, set_id):
        """
        Abstraction of a Murphy resource protocol message containing a
        resource set destruction request

        :param seq_num: Sequence number of this message
        :param set_id:  Integer ID of the resource set to destroy
        """
        super(ResourceSetDestruction, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_DESTROY_RESOURCE_SET)
        self.add_field(RESPROTO_RESOURCE_SET_ID, set_id)


class ResourceSetAcquisition(DefaultMessage):
    def __init__(self, seq_num, set_id):
        """
        Abstraction of a Murphy resource protocol message containing a
        resource set acquisition request

        :param seq_num: Sequence number of this message
        :param set_id:  Integer ID of the resource set to acquire
        """
        super(ResourceSetAcquisition, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_ACQUIRE_RESOURCE_SET)
        self.add_field(RESPROTO_RESOURCE_SET_ID, set_id)


class ResourceSetRelease(DefaultMessage):
    def __init__(self, seq_num, set_id):
        """
        Abstraction of a Murphy resource protocol message containing a
        resource set release request

        :param seq_num: Sequence number of this message
        :param set_id:  Integer ID of the resource set to acquire
        """
        super(ResourceSetRelease, self).__init__(seq_num)
        self.add_field(RESPROTO_REQUEST_TYPE, RESPROTO_RELEASE_RESOURCE_SET)
        self.add_field(RESPROTO_RESOURCE_SET_ID, set_id)


class Attribute(object):
    def __init__(self, name, data_type, value):
        """
        Abstraction of a Murphy resource attribute

        :param name:      Name of attribute
        :param data_type: Integer representing the data type of this attribute
        :param value:     Value contained in this attribute
        """
        self._name = name
        self._data_type = data_type
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def data_type(self):
        return self._data_type

    @property
    def value(self):
        return self._value

    def pretty_print(self):
        """
        Returns a human-readable representation of this Attribute instance

        :return: String containing the human-readable representation of this
                 Attribute instance
        """
        return "      %s -> %s (%s)\n" % (self.name, self.value, data_type_to_string(self.data_type))


class Resource(object):
    def __init__(self):
        """
        Abstraction of a Murphy resource
        """
        self._data = dict()

        self._attributes = dict()

    @property
    def id(self):
        """
        Internal resource ID that is used to define the mask for this resource

        :return: None if not available yet, integer representing the resource ID otherwise
        """
        return self._data.get("id")

    @id.setter
    def id(self, val):
        self._data.update({"id": val})

    @property
    def name(self):
        """
        Name of this resource

        :return: None if not available yet, string representing the resource's name otherwise
        """
        return self._data.get("name")

    @name.setter
    def name(self, val):
        self._data.update({"name": val})

    @property
    def shareable(self):
        """
        Boolean value representing if this resource can be shared

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("shareable", False)

    @shareable.setter
    def shareable(self, val):
        self._data.update({"shareable": val})

    @property
    def mandatory(self):
        """
        Boolean value representing if this resource is mandatory for this set

        :return: True if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("mandatory", True)

    @mandatory.setter
    def mandatory(self, val):
        self._data.update({"mandatory": val})

    @property
    def acquired(self):
        """
        Boolean value representing if this resource is acquired

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("acquired", False)

    @acquired.setter
    def acquired(self, val):
        self._data.update({"acquired": val})

    @property
    def available(self):
        """
        Boolean value representing if this resource is available for acquisition

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("available", False)

    @available.setter
    def available(self, val):
        self._data.update({"available": val})

    @property
    def attributes(self):
        """
        Dictionary containing the names of this resource's attributes as keys, and
        the related Attribute objects as values

        :return: Dictionary with attribute names as keys and the Attribute objects
                 as values
        """
        return self._attributes

    def add_attribute(self, attr):
        """
        Adds an Attribute object to the dictionary of attributes for this resource

        :param attr: Attribute object to add to the dictionary
        :return:     Void
        """
        self._attributes[attr.name] = attr

    def update(self, data):
        """
        Updates the contained value dictionary

        :param data: Dictionary that contains the new information to update against
        :return:     Void
        """
        self._data.update(data)

    @property
    def data(self):
        """
        Returns the internal Dictionary containing the values set in this
        resource

        :return: Dictionary containing the values set in this resource
        """
        return self._data

    def copy(self):
        """
        Creates a copy of this resource

        :return: Resource object that is a copy of the called one
        """
        res = Resource()
        res.update(self._data)

        for attr in self.attributes.values():
            res.add_attribute(Attribute(attr.name, attr.data_type, attr.value))

        return res

    def pretty_print(self):
        """
        Returns a human-readable representation of this Resource instance

        :return: String containing the human-readable representation of this
                 Resource instance
        """
        string = "  Resource %s:\n" \
                 "    Shareable: %s\n" \
                 "    Mandatory: %s\n" \
                 "    Acquired: %s\n" \
                 "    Available: %s\n\n" \
                 "    Attributes:\n" % (self.name, self.shareable, self.mandatory, self.acquired, self.available)

        for attr in self.attributes.values():
            string += attr.pretty_print()

        return string + "\n"


class ResourceSet(object):
    def __init__(self):
        """
        Abstraction of a Murphy resource set
        """
        self._data = dict()
        self._resources = dict()

    @property
    def id(self):
        """
        Resource set ID

        :return: None if not available yet, integer representing the resource set ID otherwise
        """
        return self._data.get("id")

    @id.setter
    def id(self, val):
        self._data["id"] = val

    @property
    def acquired(self):
        """
        Boolean value representing if this resource set is acquired

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("acquired", False)

    @acquired.setter
    def acquired(self, val):
        self._data["acquired"] = val

    @property
    def autorelease(self):
        """
        Boolean value representing if this resource set has an autorelease flag set

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("autorelease", False)

    @autorelease.setter
    def autorelease(self, val):
        self._data["autorelease"] = val

    @property
    def autoacquire(self):
        """
        Boolean value representing if this resource set has an autoacquire flag set

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("autoacquire", False)

    @autoacquire.setter
    def autoacquire(self, val):
        self._data["autoacquire"] = val

    @property
    def no_events(self):
        """
        Boolean value representing if this resource set has a 'no events' flag set

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("no_events", False)

    @no_events.setter
    def no_events(self, val):
        self._data["no_events"] = val

    @property
    def dont_wait(self):
        """
        Boolean value representing if this resource set has a "don't wait" flag set

        :return: False if not set yet, boolean value set for this flag otherwise
        """
        return self._data.get("dont_wait", False)

    @dont_wait.setter
    def dont_wait(self, val):
        self._data["dont_wait"] = val

    @property
    def priority(self):
        """
        Integer value representing the priority value of this resource set

        :return: Zero if not set yet, integer value representing the priority value set otherwise
        """
        return self._data.get("priority", 0)

    @priority.setter
    def priority(self, val):
        self._data["priority"] = val

    @property
    def resources(self):
        """
        Returns the dictionary of resources included in this resource set

        :return: Dictionary with resource names as keys, and related Resource objects
                 as values
        """
        return self._resources

    def add_resource(self, res):
        """
        Adds a resource to this resource set

        :param res: Resource instance to add to this resource set
        :return:    Void
        """
        self._resources[res.name] = res

    def update(self, data):
        """
        Updates the contained value dictionary

        :param data: Dictionary that contains the new information to update against
        :return:     Void
        """
        self._data.update(data)

    @property
    def data(self):
        """
        Returns the internal Dictionary containing the values set in this
        resource set

        :return: Dictionary containing the values set in this resource
        """
        return self._data

    def copy(self):
        """
        Creates a copy of this resource set

        :return: ResourceSet object that is a copy of the called one
        """
        res_set = ResourceSet()
        res_set.update(self.data)

        for res in self.resources.values():
            res_set.add_resource(res.copy())

        return res_set

    def pretty_print(self):
        """
        Returns a human-readable representation of this ResourceSet instance

        :return: String containing the human-readable representation of this
                 ResourceSet instance
        """
        string = "Resource Set %s:\n" \
                 "  Acquired: %s\n" \
                 "  Resources:\n\n" % (self.id, self.acquired)

        for res in self.resources.values():
            string += res.pretty_print()

        return string


class Field(object):
    def __init__(self, field_type, data_type, field_value):
        """
        Abstraction of a single field in a Murphy resource protocol message

        :param field_type:  Integer representing the type of this field
        :param data_type:   Integer representing the data type of this field
        :param field_value: Value contained in this field
        :return:
        """
        self.__field_type = field_type
        self.__data_type = data_type
        self.__field_value = field_value

    @property
    def type(self):
        return self.__field_type

    @property
    def data_type(self):
        return self.__data_type

    @property
    def value(self):
        return self.__field_value


class MurphyConnection(asyncore.dispatcher_with_send):
    def __init__(self, address, daemonize=True):
        """
        Abstracts a connection to Murphy

        :param address:   Address to a Murphy socket, in the format shared with libmurphy-resource.
                          Is given in the format "socket_type:address", where socket_type can be
                          one of the following:
                            * unxs [unix socket]
                            * tcp4 [ipv4 tcp socket]
                            * tcp6 [ipv6 tcp socket]

                          Additionally, with unix sockets one can prefix the socket name with @,
                          which will use an abstract unix socket
        :param daemonize: Optional boolean, defaults to True. Defines whether or not the internal
                          socket thread is created as daemon or not
        :raises:          ValueError in case the protocol type was unknown
        """
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

        self._internal_set = ResourceSet()

        self._running = True
        self.thread = Thread(target=self.run_loop)
        self.thread.daemon = daemonize
        self.thread.start()

    def close(self):
        """
        Closes the socket, effectively ending the usage of this object

        :return: Void
        """
        self._running = False
        self.socket.shutdown(SHUT_RDWR)
        asyncore.dispatcher_with_send.close(self)

    def run_loop(self):
        """
        Runs the socket reading loop until the closing is initialized

        :return: Void
        """
        while self._running:
            asyncore.loop(count=1)

    def read_message(self, read_buffer):
        """
        Reads enough data from a buffer and the socket until a full message is received

        :param read_buffer: Byte string buffer that is currently being handled
        :return:            Tuple containing the read byte string buffer that starts
                            with the read message, as well as the length of the buffer
                            occupied by the read message
        """
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
        """
        Checks if a MurphyMessage is a response to something we sent

        :param message: MurphyMessage instance to parse
        :return:        Void
        """
        queue = self.queue.contents

        seq_num = message.seq_num
        req_type = message.req_type

        # Is this an event?
        if req_type is RESPROTO_RESOURCES_EVENT:
            print("D: Got an event! (seq %s - type %s)" % (message.seq_num, request_type_to_string(req_type)))

            if seq_num in queue and req_type in queue.get(seq_num):
                print("D: Got an event that is a response to a sent message!")
                queue.get(seq_num, {}).get(req_type).set_result(message)
                return
            else:
                self.events.append(message)

        # Or something expected in general?
        elif seq_num in queue and req_type in queue.get(seq_num):
            print("D: Got a response to a sent message! (seq %s - type %s)" % (seq_num,
                                                                               request_type_to_string(req_type)))
            queue.get(seq_num, {}).get(req_type).set_result(message)
            return

        # Or just something completely else?
        else:
            print("D: Got unrelated message (seq %s - type %s)" % (seq_num, request_type_to_string(req_type)))

    def parse_event(self, event_msg):
        """
        Parses an event's information from a MurphyMessage instance, and applies
        the updated information to one of the internally kept state sets in case
        the event is for one of them

        :param event_msg: MurphyMessage that contains an event
        :return:          None if the message contains no resource set ID,
                          False if the included resource set ID is not one of
                          the currently known ones and True if one of the internal
                          sets was successfully updated
        """
        res_set = parse_message_to_resource_set(event_msg)
        if res_set.id is None:
            print("E: No set id in event!")
            return None

        set_id = res_set.id

        if set_id in self.own_sets:
            print("D: We found an event for set %s" % (set_id))
            parse_message_to_resource_set(event_msg, self.own_sets.get(set_id))
            return True
        else:
            print("D: We found an event for a set that is not yet in our books (id = %s)" % (set_id))
            return False

    def parse_received_events(self):
        """
        Checks received events and updates internally kept states, meant
        for manual calling outside of callbacks

        :return: None if no events were received, True if events were parsed
        """
        if not self.events:
            return None

        for event in list(self.events):
            result = self.parse_event(event)

            # Either the event was invalid or a set was updated with its information,
            # remove the event from the list
            if result is None or result:
                self.events.remove(event)
            # Otherwise we just keep iterating

        return True

    def handle_read(self):
        """
        Implements the reading of Murphy resource protocol messages from a
        socket.

        :return: Void
        """
        # Do an initial read
        read_buffer = self.recv(MRP_DEFAULT_RECEIVE_SIZE)

        while len(read_buffer) > 0:
            read_buffer, message_size = self.read_message(read_buffer)
            message = parse_message(read_buffer)
            self.check_message(message)
            print(message.pretty_print())
            read_buffer = read_buffer[message_size:]
            print("Reader length: %s" % (len(read_buffer)))

    def send_message(self, byte_string):
        """
        Sends a message in byte string form to the Murphy server

        :param byte_string: Byte string containing a Murphy resource protocol
                            message
        :return:            Void
        """
        amount_to_write = len(byte_string)

        self.send(pack("!L", amount_to_write) + byte_string)

    @property
    def next_seq_num(self):
        """
        Returns the current value of the internal counter for sequence numbers,
        and increments it by one.

        :return: Integer value representing the current value of the internal
                 counter for sequence numbers
        """
        current = self._internal_counter
        self._internal_counter += 1
        return current

    def send_request(self, message):
        """
        Sends a request to Murphy and waits for a response

        :param message: MurphyMessage instance the contents of which to send
        :return:        None if a failure occurred, a MurphyMessage object
                        otherwise.
        """
        status = Status()

        self.queue.add(message.req_type, message.seq_num, status)

        self.send_message(message.convert_to_byte_string())

        gatekeeper = status.wait(MRP_DEFAULT_TIMEOUT)

        # If gatekeeper tells us that we didn't get a response, we timed out
        if not gatekeeper:
            print("E: Timed out on the response (waited five seconds; seq %s - type %s)" % (message.seq_num,
                                                                                            message.req_type))
            self.queue.remove(message.req_type, message.seq_num)
            return None

        # Get the response data from the status object
        response = status.get_result()
        self.queue.remove(message.req_type, message.seq_num)

        # Check the status value of the response
        for field in response.fields:
            if field.type is RESPROTO_REQUEST_STATUS and field.value:
                print("E: Request status error code is nonzero! (%s)" % (field.value))
                return None

        # Delete the status object itself
        del(status)

        return response

    def send_request_with_event(self, message):
        """
        Sends a request to Murphy and waits for both a response as well as an event

        :param message: MurphyMessage instance the contents of which to send
        :return:        None if a failure occurred, a MurphyMessage object
                        otherwise
        """
        status = Status()

        # The event that should come if the creation is successful
        self.queue.add(RESPROTO_RESOURCES_EVENT, message.seq_num, status)

        response = self.send_request(message)
        if response is None:
            print("E: Failed to gain reply or reply was a failure (seq %d - type %d)" % (message.seq_num,
                                                                                         message.req_type))
            self.queue.remove(RESPROTO_RESOURCES_EVENT, message.seq_num)
            return None

        # We wait for the event
        gatekeeper = status.wait(MRP_DEFAULT_TIMEOUT)

        # If gatekeeper tells us that we didn't get a response, we timed out
        if not gatekeeper:
            print("E: Timed out on the event (waited five seconds; seq %d - type %d)" % (message.seq_num,
                                                                                         message.req_type))
            self.queue.remove(RESPROTO_RESOURCES_EVENT, message.seq_num)
            return None

        # Get the response data from the status object
        response = status.get_result()
        self.queue.remove(RESPROTO_RESOURCES_EVENT, message.seq_num)

        # Delete the status object itself
        del(status)

        return response

    def list_resources(self):
        """
        Lists the resources available in the Murphy server

        :return: None if a failure occurred, a list containing the names
                 of resources otherwise
        """
        response = self.send_request(ResourceListing(self.next_seq_num))
        if response is None:
            print("E: Resource listing request failed")
            return None

        names = []

        res_set = parse_message_to_resource_set(response)

        self._internal_set = res_set

        for resource in res_set.resources.values():
            names.append(resource.name)

        return names

    def list_classes(self):
        """
        Lists the application classes available in the Murphy server

        :return: None if a failure occurred, a list containing the names of
                 application classes otherwise
        """
        response = self.send_request(ApplicationClassListing(self.next_seq_num))
        if response is None:
            print("E: Application class listing request failed!")
            return None

        for field in response.fields:
            if field.type is RESPROTO_CLASS_NAME:
                return field.value

        print("E: Class listing in application class listing request not found!")
        return None

    def list_zones(self):
        """
        Lists the zones available in the Murphy server

        :return: None if failure occurred, a list containing the names of
                 zones otherwise
        """
        response = self.send_request(ZoneListing(self.next_seq_num))
        if response is None:
            print("E: Zone listing request failed")
            return None

        for field in response.fields:
            if field.type is RESPROTO_ZONE_NAME:
                return field.value

        print("E: Zone listing in zone listing request not found!")
        return None

    def get_resource(self, res_name):
        """
        Gets a copy of a resource from the internal listing, usable for
        resource set creation

        :param res_name: Name of resource to add
        :return:         None if resource by such name is not available,
                         a Resource object otherwise
        """
        resource = self._internal_set.resources.get(res_name)
        if resource is None:
            return None

        return resource.copy()

    def create_set(self, res_set, app_class, zone):
        """
        Sends out a resource set creation request to create a resource set
        on the server side for this client

        :param res_set:   ResourceSet instance describing the resource set to be created
        :param app_class: Application class to which the created resource set will be set
        :param zone:      Zone to which the created resource set will be set
        :return:          None if a failure occurred, integer representing the newly created
                          resource set's ID otherwise
        """
        set_id = None

        message = ResourceSetCreation(self.next_seq_num, res_set, app_class, zone)

        response = self.send_request_with_event(message)
        if response is None:
            print("E: Set creation failed")

        for field in response.fields:
            if field.type is RESPROTO_RESOURCE_SET_ID:
                set_id = field.value
                break

        parse_message_to_resource_set(response, res_set)
        self.own_sets[res_set.id] = res_set

        return set_id

    def destroy_set(self, set_id):
        """
        Sends out a resource set destruction request to destroy a given set on the
        server side for this client

        :param set_id: Integer representing the resource set's ID to be destroyed
        :return:       None if failure occurred, True if set was successfully destroyed
        """
        response = self.send_request(ResourceSetDestruction(self.next_seq_num, set_id))
        if response is None:
            print("E: Zone listing request failed")
            return None

        # The resource set was successfully destroyed, remove it from the internal list
        del(self.own_sets[set_id])

        return True

    def acquire_set(self, set_id):
        """
        Sends out a resource set acquisition request to acquire a given set on the server
        side for this client

        :param set_id: Integer representing the resource set's ID to be acquired
        :return:       None if failure occurred, boolean that notes whether or not the
                       resource set was acquired. For a more detailed result, get_state()
                       can be used
        """
        message = ResourceSetAcquisition(self.next_seq_num, set_id)

        response = self.send_request_with_event(message)
        if response is None:
            print("E: Set acquisition query failed")
            return None

        for field in response.fields:
            if field.type is RESPROTO_RESOURCE_STATE:
                parse_message_to_resource_set(response, self.own_sets.get(set_id))
                return bool(field.value)

        print("E: Failed to find set state from the event!")
        return None

    def release_set(self, set_id):
        """
        Sends out a resource set release request to release a given set on the server
        side for this client

        :param set_id: Integer representing the resource set's ID to be acquired
        :return:       None if failure occurred, boolean that notes whether or not the
                       resource set was released. For a more detailed result, get_state()
                       can be used
        """
        message = ResourceSetRelease(self.next_seq_num, set_id)

        response = self.send_request_with_event(message)
        if response is None:
            print("E: Set release query failed")
            return None

        for field in response.fields:
            if field.type is RESPROTO_RESOURCE_STATE:
                parse_message_to_resource_set(response, self.own_sets.get(set_id))
                return not bool(field.value)

        print("E: Failed to find set state from the event!")
        return None

    def get_state(self, set_id):
        """
        Returns the current state of a resource set kept in the internal data structure

        :param set_id: Integer representing the resource set's ID for which a state is requested
        :return:       None if a resource set with a given ID was not found, a ResourceSet instance
                       otherwise
        """
        res_set = self.own_sets.get(set_id)
        if res_set is not None:
            return res_set.copy()
        else:
            return None
