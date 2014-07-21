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

import os
from os.path import (dirname, realpath)
from ctypes import (Structure, Union, POINTER, pointer, CFUNCTYPE,
                    cast, c_int, c_uint, c_char, c_char_p, c_void_p,
                    c_bool, c_double, CDLL, py_object)

# For basic Py2/Py3 compatibility
try:
    xrange
except NameError:
    xrange = range

# Murphy resource-native API related defines
(MRP_RES_CONNECTED, MRP_RES_DISCONNECTED) = (0, 1)


def conn_state_to_str(state):
    """
    Returns the given Murphy connection status code as a string

    :param state: Murphy connection status to be converted to a string
    :return: String that represents the given connection status
             * connected
             * disconnected
             * unknown
    """
    return {
        MRP_RES_CONNECTED:    "connected",
        MRP_RES_DISCONNECTED: "disconnected",
    }.get(state, "unknown")

(MRP_RES_RESOURCE_LOST,
 MRP_RES_RESOURCE_PENDING,
 MRP_RES_RESOURCE_ACQUIRED,
 MRP_RES_RESOURCE_AVAILABLE) = (0, 1, 2, 3)


def res_state_to_str(state):
    """
    Returns the given Murphy resource state as a string

    :param state: Murphy resource/resource set state to be converted to a string
    :return: String that represents the given resource state
             * acquired
             * available
             * lost
             * pending
             * unknown
    """
    return {
        MRP_RES_RESOURCE_ACQUIRED:  "acquired",
        MRP_RES_RESOURCE_AVAILABLE: "available",
        MRP_RES_RESOURCE_LOST:      "lost",
        MRP_RES_RESOURCE_PENDING:   "pending",
    }.get(state, "unknown")

(MRP_RES_ERROR_NONE,
 MRP_RES_ERROR_CONNECTION_LOST,
 MRP_RES_ERROR_INTERNAL,
 MRP_RES_ERROR_MALFORMED) = (0, 1, 2, 3)


def error_to_str(error):
    """
    Returns the given Murphy connection error state as a string

    :param error: Murphy connection error state to be converted to a string
    :return: String that represents the given connection error state
             * none
             * connection lost
             * internal
             * malformed
             * unknown
    """
    return {
        MRP_RES_ERROR_NONE:            "none",
        MRP_RES_ERROR_CONNECTION_LOST: "connection lost",
        MRP_RES_ERROR_INTERNAL:        "internal",
        MRP_RES_ERROR_MALFORMED:       "malformed",
    }.get(error, "unknown")

mrp_common = None
mrp_reslib = None

mrp_in_tree = None

if os.environ.get("MRP_IN_TREE"):
    mrp_in_tree = True


def load_murphy():
    global mrp_common
    global mrp_reslib
    global mrp_in_tree

    if not mrp_common or not mrp_reslib:
        if mrp_in_tree:
            # FIXME: This fails if run in an interpreter (since __file__ is not available)
            path = dirname(realpath(__file__))

            # Load the murphy resource API library as well as the common library
            mrp_common = CDLL(path + "/../src/.libs/libmurphy-common.so")
            mrp_reslib = CDLL(path + "/../src/.libs/libmurphy-resource.so")
        else:
            mrp_common = CDLL("libmurphy-common.so")
            mrp_reslib = CDLL("libmurphy-resource.so")

load_murphy()


# Create general abstractions around the things we throw around
class MrpMainloop(Structure):
    pass


class MrpResourceCtx(Structure):
    _fields_ = [("state", c_uint),
                ("zone",  c_char_p),
                ("priv",  c_void_p)]


class MrpResourceSet(Structure):
    _fields_ = [("application_class", c_char_p),
                ("state",             c_uint),
                ("priv",              c_void_p)]


class MrpStringArray(Structure):
    _fields_ = [("num_strings", c_int),
                ("strings",     POINTER(c_char_p))]


class MrpResource(Structure):
    _fields_ = [("name",  c_char_p),
                ("state", c_uint),
                ("priv",  c_void_p)]


class MrpAttributeUnion(Union):
    _fields_ = [("string",   c_char_p),
                ("integer",  c_int),
                ("unsignd",  c_uint),
                ("floating", c_double)]


class MrpAttribute(Structure):
    _anonymous_ = ("u")
    _fields_    = [("name",  c_char_p),
                   ("type",  c_char),
                   ("u",     MrpAttributeUnion)]


class UserData(Structure):
    _fields_ = [("conn",   py_object),
                ("opaque", py_object)]


# Set the arguments/return value types for used variables
mrp_common.mrp_mainloop_create.restype = POINTER(MrpMainloop)

mrp_reslib.mrp_res_create.restype = POINTER(MrpResourceCtx)

mrp_reslib.mrp_res_destroy.argtypes = [POINTER(MrpResourceCtx)]
mrp_reslib.mrp_res_destroy.restype  = None

mrp_reslib.mrp_res_list_application_classes.argtypes = [POINTER(MrpResourceCtx)]
mrp_reslib.mrp_res_list_application_classes.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_list_resources.argtypes = [POINTER(MrpResourceCtx)]
mrp_reslib.mrp_res_list_resources.restype  = POINTER(MrpResourceSet)

mrp_reslib.mrp_res_create_resource_set.argtypes = [POINTER(MrpResourceCtx),
                                                   c_char_p, c_void_p,
                                                   c_void_p]
mrp_reslib.mrp_res_create_resource_set.restype  = POINTER(MrpResourceSet)

mrp_reslib.mrp_res_set_autorelease.argtypes = [c_bool,
                                               POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_set_autorelease.restype  = c_bool

mrp_reslib.mrp_res_delete_resource_set.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_delete_resource_set.restype  = None

mrp_reslib.mrp_res_copy_resource_set.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_copy_resource_set.restype  = POINTER(MrpResourceSet)

mrp_reslib.mrp_res_equal_resource_set.argtypes = [POINTER(MrpResourceSet),
                                                  POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_equal_resource_set.restype  = c_bool

mrp_reslib.mrp_res_acquire_resource_set.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_acquire_resource_set.restype  = c_int

mrp_reslib.mrp_res_release_resource_set.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_release_resource_set.restype  = c_int

mrp_reslib.mrp_res_get_resource_set_id.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_get_resource_set_id.restype  = c_int

mrp_reslib.mrp_res_create_resource.argtypes = [POINTER(MrpResourceSet),
                                               c_char_p, c_bool, c_bool]
mrp_reslib.mrp_res_create_resource.restype  = POINTER(MrpResource)

mrp_reslib.mrp_res_list_resource_names.argtypes = [POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_list_resource_names.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_get_resource_by_name.argtypes = [POINTER(MrpResourceSet),
                                                    c_char_p]
mrp_reslib.mrp_res_get_resource_by_name.restype  = POINTER(MrpResource)

mrp_reslib.mrp_res_delete_resource.argtypes = [POINTER(MrpResource)]
mrp_reslib.mrp_res_delete_resource.restype  = None

mrp_reslib.mrp_res_delete_resource_by_name.argtypes = [POINTER(MrpResourceSet),
                                                       c_char_p]
mrp_reslib.mrp_res_delete_resource_by_name.restype  = c_bool

mrp_reslib.mrp_res_list_attribute_names.argtypes = [POINTER(MrpResource)]
mrp_reslib.mrp_res_list_attribute_names.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_get_attribute_by_name.argtypes = [POINTER(MrpResource),
                                                     c_char_p]
mrp_reslib.mrp_res_get_attribute_by_name.restype  = POINTER(MrpAttribute)

mrp_reslib.mrp_res_set_attribute_string.argtypes = [POINTER(MrpAttribute),
                                                    c_char_p]
mrp_reslib.mrp_res_set_attribute_string.restype  = c_int

mrp_reslib.mrp_res_set_attribute_uint.argtypes = [POINTER(MrpAttribute),
                                                  c_uint]
mrp_reslib.mrp_res_set_attribute_uint.restype  = c_int

mrp_reslib.mrp_res_set_attribute_int.argtypes = [POINTER(MrpAttribute),
                                                 c_int]
mrp_reslib.mrp_res_set_attribute_int.restype  = c_int

mrp_reslib.mrp_res_set_attribute_double.argtypes = [POINTER(MrpAttribute),
                                                    c_double]
mrp_reslib.mrp_res_set_attribute_double.restype  = c_int

mrp_reslib.mrp_res_free_string_array.argtypes = [POINTER(MrpStringArray)]
mrp_reslib.mrp_res_free_string_array.restype  = None

mrp_common.mrp_mainloop_destroy.restype = None


def map_attr_type_to_py_type(attr_type):
    """
    Converts a Murphy attribute type to a Python basic type

    :param attr_type: Character that represents a given attribute's type
    :return: Python basic type that represents the type of a given attribute
    """
    return {
        "i": int,
        "u": int,
        "f": float,
        "s": str,
    }.get(attr_type)


class Attribute(object):
    def __init__(self, res, name):
        """
        Gets the according attribute out of a given resource. Usually called by a Resource object.

        :param res:  Resource the attribute belongs to
        :param name: Name of the attribute to return
        :return: Attribute object created according to the parameters
        """
        self.res  = res
        self.attr = None

        self.attr = \
            mrp_reslib.mrp_res_get_attribute_by_name(pointer(res.res),
                                                     name).contents

        if not self.attr:
            raise MemoryError

    def set_value_to(self, value):
        """
        Sets the value of this attribute according to the parameter

        :param value: Value to be set in this attribute
        :return: Boolean that notes if the action was successful or not
        """
        value_type = self.attr.type
        ret_val = 1

        if value_type == "\0":
            return False

        if not isinstance(value, map_attr_type_to_py_type(value_type)):
            return False

        if isinstance(value, int):
            if value_type == "i":
                ret_val = mrp_reslib.mrp_res_set_attribute_int(pointer(self.attr), value)
            elif value_type == "u":
                if value < 0:
                    return False
                else:
                    ret_val = mrp_reslib.mrp_res_set_attribute_uint(pointer(self.attr), value)
            else:
                return False

        elif isinstance(value, float):
            ret_val = mrp_reslib.mrp_res_set_attribute_double(pointer(self.attr), value)
        elif isinstance(value, str):
            ret_val = mrp_reslib.mrp_res_set_attribute_string(pointer(self.attr), value)
        else:
            return False

        return bool(not ret_val)

    def get_type(self):
        """
        Returns the type of this attribute as a single character

        :return: Character that represents the type of this attribute.
                 * i (signed 32bit integer)
                 * u (unsigned 32bit integer)
                 * f (double floating point value)
                 * s (string)
        """
        return self.attr.type

    def get_value(self):
        """
        Returns the value currently set to this attribute.

        :return: Value currently set to this attribute
        """
        attr_type = self.attr.type

        if attr_type == "i":
            return self.attr.integer
        elif attr_type == "u":
            return self.attr.unsignd
        elif attr_type == "f":
            return self.attr.floating
        elif attr_type == "s":
            return self.attr.string
        else:
            return None

    def get_name(self):
        """
        Returns the name of this attribute.

        :return: Name of this attribute
        """
        return self.attr.name


class Resource(object):
    def __init__(self, res_set, name, mandatory=True, shared=False):
        """
        Creates (adds) a resource to a specific resource set. Has a name, status as well as an arbitrary amount of
        attributes. The names and attributes are set in the Murphy configuration, and cannot be modified
        on the fly. Attributes' values are application-specific, so there is no callback related to modification of
        those.

        :param res_set:   Resource set to which this resource will be added
        :param name:      Name of the resource to be added
        :param mandatory: Optional boolean parameter that notes whether or not this resource is
                          mandatory for a given resource set to work correctly. If set to True (default), in case
                          this resource is not acquired, it will cause the acquisition process to fail instead
                          of letting the user acquire a partial set of resources.
        :param shared:    Optional boolean parameter that notes whether or not this resource can be shared
                          with other clients. By default set to False.
        :return: Resource object created according to the parameters
        """
        self.res_set = res_set
        res = \
            mrp_reslib.mrp_res_create_resource(res_set.res_set,
                                               name, mandatory,
                                               shared)

        if not res:
            raise MemoryError

        self.res = res.contents

    def delete(self):
        """
        Deletes (removes) this resource from a given resource set

        :return: Void
        """
        self.res_set.delete_resource(self)

    def list_attribute_names(self):
        """
        Creates a list of the names of available attributes in this resource

        :return: List of the names of attributes in this resource
        """
        attribute_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_attribute_names(pointer(self.res))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                attribute_list.append(mrp_list.contents.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)

        return attribute_list

    def get_attribute_by_name(self, name):
        """
        Returns an Attribute object of the attribute that carries the given name in this resource

        :param name: Name of the attribute to return
        :return: None in case of failure, an Attribute object in case of success
        """
        attr = None

        try:
            attr = Attribute(self, name)
        except:
            return None

        return attr

    def get_state(self):
        """
        Returns the state of this resource as a string

        :return: String that represents the last updated state of this resource
                 * acquired
                 * available
                 * lost
                 * pending
                 * unknown
        """
        return res_state_to_str(self.res.state)

    def get_name(self):
        """
        Returns the name of this resource as a string

        :return: String that represents the name of this resource
        """
        return self.res.name


class GivenResource(Resource):
    def __init__(self, res_set, res):
        """
        Creates a basic Resource object based on the parameters given

        :param res_set: Resource set under which this resource will be added
        :param res:     Ctypes resource pointer pointed to the resource to be added
        :return: GivenResource object created according to the parameters
        """
        self.res_set = res_set
        self.res     = res.contents


class ResourceSet(object):
    def __init__(self, res_cb, conn, mrp_class):
        """
        Creates a resource set, which is the basic unit of acquiring and releasing resources. Resources can be
        acquired or lost independently if the configuration permits, but the client can only request and release
        whole resource sets. Usually used via Connection.create_resource_set() and not directly.

        :param res_cb:    Resource callback to be called when there is an update in this resource set
        :param conn:      Connection to which this ResourceSet belongs
        :param mrp_class: Application class to which this resource set belongs
        :return: ResourceSet object created according to the parameters
        """
        self.conn      = conn
        self.res_cb    = res_cb

        # Create a python callback for resources
        res_callbackfunc = CFUNCTYPE(None, POINTER(MrpResourceCtx),
                                     POINTER(MrpResourceSet),
                                     c_void_p)

        def res_callback_func(res_ctx_p, res_set_p, userdata_p):
            opaque = cast(userdata_p, POINTER(UserData)).contents.opaque

            passed_conn    = GivenConnection(res_ctx_p)
            passed_res_set = GivenResourceSet(passed_conn, res_set_p)

            # Call the actual higher-level python callback func
            self.res_cb(passed_res_set, opaque)

        self.res_callback = res_callbackfunc(res_callback_func)

        res_set = \
            mrp_reslib.mrp_res_create_resource_set(pointer(conn.res_ctx),
                                                   mrp_class,
                                                   self.res_callback,
                                                   pointer(conn.udata))

        if not res_set:
            raise MemoryError

        self.res_set = res_set.contents

    def acquire(self):
        """
        Attempts to acquire the resources in this resource set. Success here only means that the call succeeded,
        and actual changes to the resource set's status will only be visible within a related resource callback.

        :return: Tuple of boolean and a string; The boolean is True when the order was successfully completed,
                 and False when not. The string represents one of the Murphy error states.
                 * none
                 * connection lost
                 * internal
                 * malformed
                 * unknown
        """
        ret_val = \
            mrp_reslib.mrp_res_acquire_resource_set(pointer(self.res_set))
        if not ret_val:
            return True, error_to_str(ret_val)
        else:
            return False, error_to_str(ret_val)

    def release(self):
        """
        Releases the resources in this resource set.

        :return: Tuple of boolean and a string; The boolean is True when the order was successfully completed,
                 and False when not. The string represents one of the Murphy error states.
                 * none
                 * connection lost
                 * internal
                 * malformed
                 * unknown
        """
        ret_val = \
            mrp_reslib.mrp_res_release_resource_set(pointer(self.res_set))

        if not ret_val:
            return True, error_to_str(ret_val)
        else:
            return False, error_to_str(ret_val)

    def get_id(self):
        """
        Gets the numeric ID of this resource set.

        :return: Numeric ID of this resource set
        """
        return \
            mrp_reslib.mrp_res_get_resource_set_id(pointer(self.res_set))

    def create_resource(self, name, mandatory=True, shared=False):
        """
        Creates (adds) a resource to this resource set. The mandatory and shared flags can only be set
        during resource creation, so if they have to be set to specific values, they should be set here.

        :param name:      Name of the resource to add to this resource set
        :param mandatory: Optional boolean parameter that notes whether or not this resource is
                          mandatory for this resource set to work correctly. If set to True (default), in case
                          this resource is not acquired, it will cause the acquisition process to fail instead
                          of letting the user acquire a partial set of resources.
        :param shared:    Optional boolean parameter that notes whether or not this resource can be shared
                          with other clients. By default set to False.

        :return: Resource object created according to the parameters given
        """
        return Resource(self, name, mandatory, shared)

    def list_resource_names(self):
        """
        Creates a list of the names of available resources in this resource set

        :return: List of the names of resources in this resource set
        """
        names = []

        mrp_list = \
            mrp_reslib.mrp_res_list_resource_names(pointer(self.res_set))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                names.append(mrp_list.contents.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)

        return names

    def get_resource_by_name(self, name):
        """
        Returns a Resource object of the resource that carries the given name in this resource set

        :param name: Name of the resource to return
        :return:     None in case of failure, a GivenResource object in case of success
        """
        resource = None

        mrp_res = \
            mrp_reslib.mrp_res_get_resource_by_name(pointer(self.res_set),
                                                    name)

        if mrp_res:
            resource = GivenResource(self, mrp_res)

        return resource

    @staticmethod
    def delete_resource(res):
        """
        Deletes (removes) a resource from this resource set.

        :param res: Resource to be removed from this resource set
        :return: Void
        """
        mrp_reslib.mrp_res_delete_resource(pointer(res.res))

    def delete_resource_by_name(self, name):
        """
        Deletes (removes) a resource from this resource set that carries the given name
        in this resource set.

        :param name: Name of the resource to be removed from this resource set
        :return: Boolean that notes if the action was successful or not
        """
        return bool(mrp_reslib.mrp_res_delete_resource_by_name(pointer(self.res_set),
                                                               name))

    def get_state(self):
        """
        Returns the state of this resource set as a string

        :return: String that represents the last updated state of this resource set
                 * acquired
                 * available
                 * lost
                 * pending
                 * unknown
        """
        return res_state_to_str(self.res_set.state)

    def equals(self, other):
        """
        Checks if this resource set in general equals another given resource set

        :param other: Other ResourceSet object against which to compare
        :return: Boolean that notes if the resource sets were equal or not
        """
        return bool(mrp_reslib.mrp_res_equal_resource_set(pointer(self.res_set),
                                                          pointer(other.res_set)))

    def set_autorelease(self, status):
        """
        Sets the automatic release flag for this resource set. If set to true, if this resource set is lost, it will
        be automatically released instead of having Murphy re-acquire it for this client.

        :param status: State to which to set this flag. By default False.
        :return: Boolean that notes if the action was successful or not
        """
        return bool(mrp_reslib.mrp_res_set_autorelease(status, pointer(self.res_set)))

    def delete(self):
        """
        Deletes this resource set.

        :return: Void
        """
        mrp_reslib.mrp_res_delete_resource_set(pointer(self.res_set))
        self.res_set = None

    def update(self, other):
        """
        Updates the resource set with information from another resource set. Usually used in resource callbacks.

        :param other: Other resource set from which the information will be copied from
        :return: False in case of failure, True in case of success.
        """
        mrp_res_set = \
            mrp_reslib.mrp_res_copy_resource_set(pointer(other.res_set))
        if mrp_res_set:
            if self.res_set:
                self.delete()
            self.res_set = mrp_res_set.contents
            return True
        else:
            return False


class ResourceListing(ResourceSet):
    def __init__(self, conn):
        """
        Creates a basic ResourceSet object that contains all of the resources available in the system.

        :param conn: Connection to which this resource set is to be created to
        :return: ResourceListing object with the parameters you have given
        """
        self.conn = conn

        res_set = \
            mrp_reslib.mrp_res_list_resources(self.conn.res_ctx)

        if not res_set:
            raise MemoryError

        self.res_set = res_set.contents


class GivenResourceSet(ResourceSet):
    def __init__(self, conn, res_set):
        """
        Creates a basic ResourceSet object based on the parameters given

        :param conn:    Connection object to which this object will be connected
        :param res_set: Murphy ctypes resource set around which this object will be made
        :return: ResourceListing object with the parameters you have given
        """
        self.conn = conn
        self.res_set = res_set.contents


class Connection(object):
    def __init__(self, status_cb, opaque_data):
        """
        Creates a new connection and sets the status callback as well as the opaque user data object.
        The connect() function actually creates the mainloop and initiates the connection, and the
        disconnect() function will disconnect and clean up.

        :param status_cb:   Function to call when a status callback is called. Will be called with three
                            parameters: the connection, the Murphy error state as a string as well as the opaque data
        :param opaque_data: A python object that will be passed to the callbacks under this connection
        """
        self.udata    = UserData(self, opaque_data)
        self.mainloop = None
        self.res_ctx  = None
        self.status_cb = status_cb
        self.conn_status_callback = None

        self.conn_status_callback_called = False
        self.connected_to_murphy = False

        def conn_status_callback_func(res_ctx_p, orig_error_code, userdata_p):
            self.conn_status_callback_called = True
            conn = GivenConnection(res_ctx_p)
            error_code = error_to_str(orig_error_code)
            if error_code == "none" and conn.get_state() == "connected":
                self.connected_to_murphy = True

            opaque = cast(userdata_p, POINTER(UserData)).contents.opaque

            # Call the actual Python-level callback func
            self.status_cb(conn, error_code, opaque)

        # Create the connection status callback
        conn_status_callbackfunc = CFUNCTYPE(None, POINTER(MrpResourceCtx),
                                             c_uint, c_void_p)
        self.conn_status_callback = \
            conn_status_callbackfunc(conn_status_callback_func)

    def connect(self):
        """
        Creates the Murphy mainloop and initiates the initial connection to Murphy

        :return: Boolean that tells if you are connected or not
        """
        mainloop = mrp_common.mrp_mainloop_create()
        if not mainloop:
            self.disconnect()
            return False

        self.mainloop = mainloop.contents

        res_ctx = mrp_reslib.mrp_res_create(pointer(self.mainloop),
                                            self.conn_status_callback,
                                            pointer(self.udata))
        if not res_ctx:
            self.disconnect()
            return False

        self.res_ctx = res_ctx.contents

        while self.iterate():
            if not self.conn_status_callback_called:
                continue
            else:
                connected = self.connected_to_murphy
                if not connected:
                    self.disconnect()

                return connected

    def iterate(self):
        """
        Iterates the full Murphy mainloop once, usually results in callbacks being called and status
        updated.

        :return: Boolean that notes if the action was successful or not
        """
        if pointer(self.mainloop):
            return bool(mrp_common.mrp_mainloop_iterate(pointer(self.mainloop)))
        else:
            return False

    def run(self):
        """
        Iterates the full Murphy mainloop until you disconnect.

        :return: Boolean that notes if the action was successful or not
        """
        if pointer(self.mainloop):
            return bool(mrp_common.mrp_mainloop_run(pointer(self.mainloop)))
        else:
            return False

    def disconnect(self):
        """
        Disconnects from Murphy and destroys the mainloop, cleans up related things. Does not free resources or
        resource sets and so forth. That has to be done separately.

        :return: Void
        """
        if self.res_ctx:
            mrp_reslib.mrp_res_destroy(pointer(self.res_ctx))
            self.res_ctx = None

        if self.mainloop:
            mrp_common.mrp_mainloop_quit(pointer(self.mainloop), 0)
            mrp_common.mrp_mainloop_destroy(pointer(self.mainloop))
            self.mainloop = None

        self.reset_variables()

    def reset_variables(self):
        """
        Resets the connection-related class variables. Called from disconnect()

        :return: Void
        """
        self.conn_status_callback_called = False
        self.connected_to_murphy = False

    def create_resource_set(self, res_cb, mrp_class):
        """
        Creates a new resource set to this connection

        :param res_cb:    Resource callback to be called when there is an update in the resource set.
                          The same callback can be used for multiple resource sets, in which case the
                          user must check which resource set is the one receiving an update within the
                          callback.
        :param mrp_class: Application class to which this resource set belongs
        :return: ResourceSet object created according to the parameters
        """
        return ResourceSet(res_cb, self, mrp_class)

    def list_application_classes(self):
        """
        Creates a list of the names of available application classes

        :return: List of the names of available application classes in the system
        """
        class_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_application_classes(pointer(self.res_ctx))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                class_list.append(mrp_list.contents.strings[i])

        return class_list

    def list_resources(self):
        """
        Creates a resource set that contains all of the available resources

        :return: Resource set containing all of the resources available in the system
        """
        return ResourceListing(self)

    def get_state(self):
        """
        Returns the current connection state as a string

        :return: String containing the current connection state
                 * connected
                 * disconnected
                 * unknown
        """
        if not self.res_ctx:
            return "disconnected"
        else:
            return conn_state_to_str(self.res_ctx.state)

    def get_opaque_data(self):
        """
        Returns the opaque user set data structure

        :return: Object that was set as the opaque user set data when the connection was created
        """
        return self.udata.opaque


class GivenConnection(Connection):
    def __init__(self, res_ctx):
        """
        Creates a basic Connection object that contains the resource context from an available resource context.
        Generally used in cases where there is a need for a basic (not all functionality available) version of a
        Connection object.

        :param res_ctx: Resource context around which this object will be created
        :return: GivenConnection object that is a limited version of the Connection object
        """
        self.res_ctx = res_ctx.contents
