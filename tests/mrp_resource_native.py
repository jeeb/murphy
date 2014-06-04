#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    return {
        MRP_RES_CONNECTED:    "connected",
        MRP_RES_DISCONNECTED: "disconnected",
    }.get(state, "unknown")

(MRP_RES_RESOURCE_LOST,
 MRP_RES_RESOURCE_PENDING,
 MRP_RES_RESOURCE_ACQUIRED,
 MRP_RES_RESOURCE_AVAILABLE) = (0, 1, 2, 3)


def res_state_to_str(state):
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
    return {
        MRP_RES_ERROR_NONE:            "none",
        MRP_RES_ERROR_CONNECTION_LOST: "connection lost",
        MRP_RES_ERROR_INTERNAL:        "internal",
        MRP_RES_ERROR_MALFORMED:       "malformed",
    }.get(error, "unknown")

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = dirname(realpath(__file__))

# Load the murphy resource API library as well as the common library
mrp_common = CDLL(path + "/../src/.libs/libmurphy-common.so")
mrp_reslib = CDLL(path + "/../src/.libs/libmurphy-resource.so")


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

mrp_reslib.mrp_res_list_resource_names.argtypes = [POINTER(MrpResourceCtx), POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_list_resource_names.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_create_resource_set.argtypes = [POINTER(MrpResourceCtx),
                                                   c_char_p, c_void_p,
                                                   c_void_p]
mrp_reslib.mrp_res_create_resource_set.restype  = POINTER(MrpResourceSet)

mrp_reslib.mrp_res_set_autorelease.argtypes = [POINTER(MrpResourceCtx),
                                               c_bool,
                                               POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_set_autorelease.restype  = c_bool

mrp_reslib.mrp_res_delete_resource_set.argtypes = [POINTER(MrpResourceCtx),
                                                   POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_delete_resource_set.restype  = None

mrp_reslib.mrp_res_copy_resource_set.argtypes = [POINTER(MrpResourceCtx),
                                                 POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_copy_resource_set.restype  = POINTER(MrpResourceSet)

mrp_reslib.mrp_res_equal_resource_set.argtypes = [POINTER(MrpResourceSet),
                                                  POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_equal_resource_set.restype  = c_bool

mrp_reslib.mrp_res_acquire_resource_set.argtypes = [POINTER(MrpResourceCtx), POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_acquire_resource_set.restype  = c_int

mrp_reslib.mrp_res_release_resource_set.argtypes = [POINTER(MrpResourceCtx),
                                                    POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_release_resource_set.restype  = c_int

mrp_reslib.mrp_res_get_resource_set_id.argtypes = [POINTER(MrpResourceCtx),
                                                   POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_get_resource_set_id.restype  = c_int

mrp_reslib.mrp_res_create_resource.argtypes = [POINTER(MrpResourceCtx), POINTER(MrpResourceSet),
                                               c_char_p, c_bool, c_bool]
mrp_reslib.mrp_res_create_resource.restype  = POINTER(MrpResource)

mrp_reslib.mrp_res_list_resource_names.argtypes = [POINTER(MrpResourceCtx),
                                                   POINTER(MrpResourceSet)]
mrp_reslib.mrp_res_list_resource_names.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_get_resource_by_name.argtypes = [POINTER(MrpResourceCtx),
                                                    POINTER(MrpResourceSet),
                                                    c_char_p]
mrp_reslib.mrp_res_get_resource_by_name.restype  = POINTER(MrpResource)

mrp_reslib.mrp_res_delete_resource.argtypes = [POINTER(MrpResourceSet),
                                               POINTER(MrpResource)]
mrp_reslib.mrp_res_delete_resource.restype  = None

mrp_reslib.mrp_res_delete_resource_by_name.argtypes = [POINTER(MrpResourceSet),
                                                       c_char_p]
mrp_reslib.mrp_res_delete_resource_by_name.restype  = c_bool

mrp_reslib.mrp_res_list_attribute_names.argtypes = [POINTER(MrpResourceCtx),
                                                    POINTER(MrpResource)]
mrp_reslib.mrp_res_list_attribute_names.restype  = POINTER(MrpStringArray)

mrp_reslib.mrp_res_get_attribute_by_name.argtypes = [POINTER(MrpResourceCtx),
                                                     POINTER(MrpResource),
                                                     c_char_p]
mrp_reslib.mrp_res_get_attribute_by_name.restype  = POINTER(MrpAttribute)

mrp_reslib.mrp_res_set_attribute_string.argtypes = [POINTER(MrpResourceCtx),
                                                    POINTER(MrpAttribute),
                                                    c_char_p]
mrp_reslib.mrp_res_set_attribute_string.restype  = c_int

mrp_reslib.mrp_res_set_attribute_uint.argtypes = [POINTER(MrpResourceCtx),
                                                  POINTER(MrpAttribute),
                                                  c_uint]
mrp_reslib.mrp_res_set_attribute_uint.restype  = c_int

mrp_reslib.mrp_res_set_attribute_int.argtypes = [POINTER(MrpResourceCtx),
                                                 POINTER(MrpAttribute),
                                                 c_int]
mrp_reslib.mrp_res_set_attribute_int.restype  = c_int

mrp_reslib.mrp_res_set_attribute_double.argtypes = [POINTER(MrpResourceCtx),
                                                    POINTER(MrpAttribute),
                                                    c_double]
mrp_reslib.mrp_res_set_attribute_double.restype  = c_int

mrp_reslib.mrp_res_free_string_array.argtypes = [POINTER(MrpStringArray)]
mrp_reslib.mrp_res_free_string_array.restype  = None

mrp_common.mrp_mainloop_destroy.restype = None


class Attribute(object):
    def __init__(self, res, mrp_attr):
        self.res  = res
        self.attr = mrp_attr.contents

    def set_value_to(self, value, inttype="int"):
        if isinstance(value, int):
            if inttype == "int":
                return mrp_reslib.mrp_res_set_attribute_int(pointer(self.res.res_set.conn.res_ctx),
                                                            pointer(self.attr), value)
            elif inttype == "uint":
                if value < 0:
                    return -1
                else:
                    return mrp_reslib.mrp_res_set_attribute_uint(pointer(self.res.res_set.conn.res_ctx),
                                                                 pointer(self.attr), value)
            else:
                return -1

        elif isinstance(value, float):
            return mrp_reslib.mrp_res_set_attribute_double(pointer(self.res.res_set.conn.res_ctx),
                                                           pointer(self.attr), value)
        elif isinstance(value, str):
            return mrp_reslib.mrp_res_set_attribute_string(pointer(self.res.res_set.conn.res_ctx),
                                                           pointer(self.attr), value)
        else:
            return -1

    def get_value(self):
        return {
            "i":  self.attr.integer,
            "u":  self.attr.unsignd,
            "f":  self.attr.floating,
            "s":  self.attr.string,
            "\0": None,
        }.get(self.attr.type, None)

    def get_name(self):
        return self.attr.name


class Resource(object):
    def __init__(self, conn, res_set, name, mandatory=True, shared=False):
        self.res_set = res_set
        res = \
            mrp_reslib.mrp_res_create_resource(conn.res_ctx,
                                               res_set.res_set,
                                               name, mandatory,
                                               shared)

        if not res:
            raise MemoryError

        self.res = res.contents

    def delete(self):
        return self.res_set.delete_resource(self)

    def list_attribute_names(self):
        attribute_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_attribute_names(pointer(self.res_set.conn.res_ctx),
                                                    pointer(self.res))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                attribute_list.append(mrp_list.contents.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)

        return attribute_list

    def get_attribute_by_name(self, name):
        attr = None

        mrp_attr = \
            mrp_reslib.mrp_res_get_attribute_by_name(pointer(self.res_set.conn.res_ctx),
                                                     pointer(self.res),
                                                     name)

        if mrp_attr:
            attr = Attribute(self, mrp_attr)

        return attr

    def get_state(self):
        return res_state_to_str(self.res.state)


class GivenResource(Resource):
    def __init__(self, res_set, res):
        self.res_set = res_set
        self.res     = res.contents


class ResourceSet(object):
    def __init__(self, res_cb, conn, mrp_class):
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
        return \
            mrp_reslib.mrp_res_acquire_resource_set(pointer(self.conn.res_ctx),
                                                    pointer(self.res_set))

    def release(self):
        return \
            mrp_reslib.mrp_res_release_resource_set(pointer(self.conn.res_ctx),
                                                    pointer(self.res_set))

    def get_id(self):
        return \
            mrp_reslib.mrp_res_get_resource_set_id(pointer(self.conn.res_ctx),
                                                   pointer(self.res_set))

    def create_resource(self, name, mandatory=True, shared=False):
        res = Resource(self.conn, self, name, mandatory, shared)

        return res

    def list_resource_names(self):
        names = []

        mrp_list = \
            mrp_reslib.mrp_res_list_resource_names(pointer(self.conn.res_ctx),
                                                   pointer(self.res_set))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                names.append(mrp_list.contents.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)

        return names

    def get_resource_by_name(self, name):
        resource = None

        mrp_res = \
            mrp_reslib.mrp_res_get_resource_by_name(pointer(self.conn.res_ctx),
                                                    pointer(self.res_set),
                                                    name)

        if mrp_res:
            resource = GivenResource(self, mrp_res)

        return resource

    def delete_resource(self, res):
        return mrp_reslib.mrp_res_delete_resource(pointer(self.res_set), pointer(res.res))

    def delete_resource_by_name(self, name):
        return mrp_reslib.mrp_res_delete_resource_by_name(pointer(self.res_set),
                                                          name)

    def get_state(self):
        return res_state_to_str(self.res_set.state)

    def equals(self, other):
        return mrp_reslib.mrp_res_equal_resource_set(pointer(self.res_set),
                                                     pointer(other.res_set))

    def set_autorelease(self, status):
        return mrp_reslib.mrp_res_set_autorelease(pointer(self.conn.res_ctx),
                                                  status, pointer(self.res_set))

    def delete(self):
        mrp_reslib.mrp_res_delete_resource_set(pointer(self.conn.res_ctx),
                                               pointer(self.res_set))
        self.res_set = None

    # FIXME: I think this might be quite bad,
    #        update the original with the new one until I clean this up
    def _copy(self):
        mrp_res_set = \
            mrp_reslib.mrp_res_copy_resource_set(pointer(self.conn.res_ctx),
                                                 pointer(self.res_set))
        if mrp_res_set:
            return GivenResourceSet(self.conn, mrp_res_set.contents)
        else:
            return None

    def update(self, other):
        mrp_res_set = \
            mrp_reslib.mrp_res_copy_resource_set(pointer(other.conn.res_ctx),
                                                 pointer(other.res_set))
        if mrp_res_set:
            if self.res_set:
                self.delete()
            self.res_set = mrp_res_set.contents
            return True
        else:
            return False


class ResourceListing(ResourceSet):
    def __init__(self, conn):
        self.conn = conn

        res_set = \
            mrp_reslib.mrp_res_list_resources(self.conn.res_ctx)

        if not res_set:
            raise MemoryError

        self.res_set = res_set.contents


class GivenResourceSet(ResourceSet):
    def __init__(self, conn, res_set):
        self.conn = conn
        self.res_set = res_set.contents


class Connection(object):
    def __init__(self, status_cb, opaque_data):
        """
        Creates a new connection and sets the status callback as well as the opaque user data object.
        The connect() function actually creates the mainloop and initiates the connection, and the
        disconnect() function will disconnect and clean up.

        :param status_cb:   Function to call when a status callback is called. Will be called with three
                            parameters: the connection, the Murphy error code (int) as well as the opaque data
        :param opaque_data: A python object that will be passed to the callbacks under this connection
        """
        self.udata    = UserData(self, opaque_data)
        self.mainloop = None  # not a pointer
        self.res_ctx  = None  # not a pointer
        self.status_cb = status_cb
        self.conn_status_callback = None

        self.conn_status_callback_called = False
        self.connected_to_murphy = False

        def conn_status_callback_func(res_ctx_p, error_code, userdata_p):
            self.conn_status_callback_called = True
            conn = GivenConnection(res_ctx_p)
            if error_to_str(error_code) == "none" and conn.get_state() == "connected":
                self.connected_to_murphy = True

            opaque = cast(userdata_p, POINTER(UserData)).contents.opaque

            # Call the actual Python-level callback func
            self.status_cb(conn, error_code, opaque)

        # Create the connection status callback
        conn_status_callbackfunc = CFUNCTYPE(None, POINTER(MrpResourceCtx),
                                             c_uint, c_void_p)
        self.conn_status_callback = \
            conn_status_callbackfunc(conn_status_callback_func)

    def __deepcopy__(self, memo):
        if isinstance(self, GivenConnection):
            return GivenConnection(pointer(self.res_ctx))
        else:
            return Connection(self.status_cb, self.udata.opaque)

    def connect(self):
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
        if pointer(self.mainloop):
            return mrp_common.mrp_mainloop_iterate(pointer(self.mainloop))

    def disconnect(self):
        if self.res_ctx:
            mrp_reslib.mrp_res_destroy(pointer(self.res_ctx))
            self.res_ctx = None

        if self.mainloop:
            mrp_common.mrp_mainloop_quit(pointer(self.mainloop), 0)
            mrp_common.mrp_mainloop_destroy(pointer(self.mainloop))
            self.mainloop = None

    def create_resource_set(self, res_cb, mrp_class):
        return ResourceSet(res_cb, self, mrp_class)

    def list_application_classes(self):
        class_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_application_classes(pointer(self.res_ctx))

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                class_list.append(mrp_list.contents.strings[i])

        return class_list

    def list_resources(self):
        return ResourceListing(self)

    def get_state(self):
        if not self.res_ctx:
            return "disconnected"
        else:
            return conn_state_to_str(self.res_ctx.state)

    def get_opaque_data(self):
        return self.udata.opaque


class GivenConnection(Connection):
    def __init__(self, res_ctx):
        self.res_ctx = res_ctx.contents
