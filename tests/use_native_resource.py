#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import (dirname, realpath)
from ctypes import (Structure, Union, POINTER, pointer, CFUNCTYPE,
                    cast, c_int, c_uint, c_char, c_char_p, c_void_p,
                    c_bool, c_double, CDLL, py_object)
import sys


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


def get_type(type):
    pass

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = dirname(realpath(__file__))

# Load the murphy resource API library as well as the common library
mrp_common = CDLL(path + "/../src/.libs/libmurphy-common.so")
mrp_reslib = CDLL(path + "/../src/.libs/libmurphy-resource.so")


# Create general abstractions around the things we throw around
class Mrp_resource_ctx(Structure):
    _fields_ = [("state", c_uint),
                ("zone",  c_char_p),
                ("priv",  c_void_p)]


class Mrp_resource_set(Structure):
    _fields_ = [("application_class", c_char_p),
                ("state",             c_uint),
                ("priv",              c_void_p)]


class Mrp_string_array(Structure):
    _fields_ = [("num_strings", c_int),
                ("strings",     POINTER(c_char_p))]


class Mrp_resource(Structure):
    _fields_ = [("name",  c_char_p),
                ("state", c_uint),
                ("priv",  c_void_p)]


class Mrp_attribute_union(Union):
    _fields_ = [("string",   c_char_p),
                ("integer",  c_int),
                ("unsignd",  c_uint),
                ("floating", c_double)]


class Mrp_attribute(Structure):
    _anonymous_ = ("u")
    _fields_    = [("name",  c_char_p),
                   ("type",  c_char),
                   ("u",     Mrp_attribute_union)]


class Userdata(Structure):
    _fields_ = [("conn",   py_object),
                ("opaque", py_object)]


# Set the arguments/return value types for used variables
mrp_reslib.mrp_res_create.restype  = POINTER(Mrp_resource_ctx)

mrp_reslib.mrp_res_destroy.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_reslib.mrp_res_destroy.restype  = None

mrp_reslib.mrp_res_list_application_classes.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_reslib.mrp_res_list_application_classes.restype  = POINTER(Mrp_string_array)

mrp_reslib.mrp_res_list_resources.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_reslib.mrp_res_list_resources.restype  = POINTER(Mrp_resource_set)

mrp_reslib.mrp_res_list_resource_names.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_list_resource_names.restype  = POINTER(Mrp_string_array)

mrp_reslib.mrp_res_create_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                   c_char_p, c_void_p,
                                                   c_void_p]
mrp_reslib.mrp_res_create_resource_set.restype  = POINTER(Mrp_resource_set)

mrp_reslib.mrp_res_set_autorelease.argtypes = [POINTER(Mrp_resource_ctx),
                                               c_bool,
                                               POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_set_autorelease.restype  = c_bool

mrp_reslib.mrp_res_delete_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                   POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_delete_resource_set.restype  = None

mrp_reslib.mrp_res_copy_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                 POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_copy_resource_set.restype  = POINTER(Mrp_resource_set)

mrp_reslib.mrp_res_equal_resource_set.argtypes = [POINTER(Mrp_resource_set),
                                                  POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_equal_resource_set.restype  = c_bool

mrp_reslib.mrp_res_acquire_resource_set.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_acquire_resource_set.restype  = c_int

mrp_reslib.mrp_res_release_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_release_resource_set.restype  = c_int

mrp_reslib.mrp_res_get_resource_set_id.argtypes = [POINTER(Mrp_resource_ctx),
                                                   POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_get_resource_set_id.restype  = c_int

mrp_reslib.mrp_res_create_resource.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set),
                                               c_char_p, c_bool, c_bool]
mrp_reslib.mrp_res_create_resource.restype  = POINTER(Mrp_resource)

mrp_reslib.mrp_res_list_resource_names.argtypes = [POINTER(Mrp_resource_ctx),
                                                   POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_list_resource_names.restype  = POINTER(Mrp_string_array)

mrp_reslib.mrp_res_get_resource_by_name.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_resource_set),
                                                    c_char_p]
mrp_reslib.mrp_res_get_resource_by_name.restype  = POINTER(Mrp_resource)

mrp_reslib.mrp_res_delete_resource.argtypes = [POINTER(Mrp_resource_set),
                                               POINTER(Mrp_resource)]
mrp_reslib.mrp_res_delete_resource.restype  = None

mrp_reslib.mrp_res_delete_resource_by_name.argtypes = [POINTER(Mrp_resource_set),
                                                       c_char_p]
mrp_reslib.mrp_res_delete_resource_by_name.restype  = c_bool

mrp_reslib.mrp_res_list_attribute_names.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_resource)]
mrp_reslib.mrp_res_list_attribute_names.restype  = POINTER(Mrp_string_array)

mrp_reslib.mrp_res_get_attribute_by_name.argtypes = [POINTER(Mrp_resource_ctx),
                                                     POINTER(Mrp_resource),
                                                     c_char_p]
mrp_reslib.mrp_res_get_attribute_by_name.restype  = POINTER(Mrp_attribute)

mrp_reslib.mrp_res_set_attribute_string.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_attribute),
                                                    c_char_p]
mrp_reslib.mrp_res_set_attribute_string.restype  = c_int

mrp_reslib.mrp_res_set_attribute_uint.argtypes = [POINTER(Mrp_resource_ctx),
                                                  POINTER(Mrp_attribute),
                                                  c_uint]
mrp_reslib.mrp_res_set_attribute_uint.restype  = c_int

mrp_reslib.mrp_res_set_attribute_int.argtypes = [POINTER(Mrp_resource_ctx),
                                                 POINTER(Mrp_attribute),
                                                 c_int]
mrp_reslib.mrp_res_set_attribute_int.restype  = c_int

mrp_reslib.mrp_res_set_attribute_double.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_attribute),
                                                    c_double]
mrp_reslib.mrp_res_set_attribute_double.restype  = c_int

mrp_reslib.mrp_res_free_string_array.argtypes = [POINTER(Mrp_string_array)]
mrp_reslib.mrp_res_free_string_array.restype  = None


mrp_common.mrp_mainloop_destroy.restype = None


def py_status_callback(conn, error_code, opaque):
    if conn.get_state() == "connected":
        print("We are connected!\n")

        print("Infodump:\n")

        # Let's try getting the classes
        app_classes = conn.list_application_classes()

        for app_class in app_classes:
            print('Class: %s' % (app_class))

        # Let's try getting all the resources
        res_set = conn.list_resources()
        res_names = res_set.list_resource_names()

        for name in res_names:
            res = res_set.get_resource_by_name(name)
            attr_list = res.list_attribute_names()

            print('Resource: %s' % (name))
            for attr_name in attr_list:
                attr = res.get_attribute_by_name(attr_name)
                print("\tAttribute: %s = %s" % (attr_name, attr.get_value()))

    print('ResCtxCallback ErrCode: %d' % (error_code))


def py_res_callback(new_res_set, opaque):
    print("ResCallBack: Entered")

    # Get the old res set from the opaque data
    res_set = opaque.res_set

    # Check if this callback is for the resource set we have in userdata
    if not new_res_set:
        print("ResCallBack: No resource set yet set")
        return
    elif not res_set.equals(new_res_set):
        print("ResCallBack: Callback not for carried resource set")
        return

    # Print information about the old resource set state
    print("ResCallBack: Previously resource set was: %s" %
          (res_set.get_state()))

    # Print information about the new resource set state
    print("ResCallBack: Resource set now is: %s" %
          (new_res_set.get_state()))

    # Compare the resources, and check which ones have changed
    for resource in new_res_set.list_resource_names():
        old_resource     = res_set.get_resource_by_name(resource)
        checked_resource = new_res_set.get_resource_by_name(resource)

        if old_resource.get_state() != checked_resource.get_state():
            attr = checked_resource.get_attribute_by_name(checked_resource.list_attribute_names()[0])
            print("ResCallBack: The status of resource '%s' has changed: %s -> %s" %
                  (resource, old_resource.get_state(),
                   checked_resource.get_state()))
            print("ResCallBack: Attribute %s = %s" % (attr.get_name(), attr.get_value()))

    # Remove and switch the userdata resource set to a new one
    res_set.update(new_res_set)

    opaque.res_set_changed = True


def actual_test_steps(conn):
    # Create a clean, empty new resource set
    print("Entered actual test steps")
    res_set = conn.create_resource_set(py_res_callback, "player")
    if not res_set:
        print("Failed to create a resource set")
        return False

    # We hold the currently worked upon res_set
    # in the opaque data
    conn.udata.opaque.res_set = res_set

    # Add the audio_playback resource to the empty set
    resource = res_set.create_resource("audio_playback")
    if not resource:
        print("Can has no resource")
        return False

    attr = resource.get_attribute_by_name(resource.list_attribute_names()[0])
    attr.set_value_to("huehue")

    acquired_status = res_set.acquire()

    return not acquired_status


def check_tests_results(conn):
    # Check new status
    res_set = conn.udata.opaque.res_set
    if res_set.get_state() != "acquired":
        print("FirstTest: Something went wrong, resource set's not ours")
        return False
    else:
        print("FirstTest: Yay, checked that we now own the resource set")
        res  = res_set.get_resource_by_name("audio_playback")
        attr = res.get_attribute_by_name(res.list_attribute_names()[0])
        if attr.get_value() == "huehue":
            print("FirstTest: Yay, we have the first attribute set to 'huehue' now!")
            return True


class attribute():
    def __init__(self, res, mrp_attr):
        self.res  = res
        self.attr = mrp_attr

    def set_value_to(self, value, inttype="int"):
        if isinstance(value, int):
            if inttype == "int":
                return mrp_reslib.mrp_res_set_attribute_int(self.res.res_set.conn.res_ctx,
                                                            self.attr, value)
            elif inttype == "uint":
                if value < 0:
                    return -1
                else:
                    return mrp_reslib.mrp_res_set_attribute_uint(self.res.res_set.conn.res_ctx,
                                                                 self.attr, value)
            else:
                return -1

        elif isinstance(value, float):
            return mrp_reslib.mrp_res_set_attribute_double(self.res.res_set.conn.res_ctx,
                                                           self.attr, value)
        elif isinstance(value, str):
            return mrp_reslib.mrp_res_set_attribute_string(self.res.res_set.conn.res_ctx,
                                                           self.attr, value)
        else:
            return -1

    def get_value(self):
        return {
            "i":  self.attr.contents.integer,
            "u":  self.attr.contents.unsignd,
            "f":  self.attr.contents.floating,
            "s":  self.attr.contents.string,
            "\0": None,
        }.get(self.attr.contents.type, None)

    def get_name(self):
        return self.attr.contents.name


class resource():
    def __init__(self, conn, res_set, name, mandatory=True, shared=False):
        self.res_set = res_set
        self.res = \
            mrp_reslib.mrp_res_create_resource(conn.res_ctx,
                                               res_set.res_set,
                                               name, mandatory,
                                               shared)

        if not self.res:
            self.__del__()

    def delete(self):
        return self.res_set.delete_resource(self)

    def list_attribute_names(self):
        attribute_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_attribute_names(self.res_set.conn.res_ctx,
                                                    self.res)

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                attribute_list.append(mrp_list.contents.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)
            mrp_list = None

        return attribute_list

    def get_attribute_by_name(self, name):
        attr = None

        mrp_attr = \
            mrp_reslib.mrp_res_get_attribute_by_name(self.res_set.conn.res_ctx,
                                                     self.res,
                                                     name)

        if mrp_attr:
            attr = attribute(self, mrp_attr)

        return attr

    def get_state(self):
        return res_state_to_str(self.res.contents.state)


class given_resource(resource):
    def __init__(self, res_set, res):
        self.res_set = res_set
        self.res     = res


class resource_set():
    def __init__(self, res_cb, conn, mrp_class):
        self.conn = conn
        self.mrp_class = mrp_class
        self.res_cb = res_cb

        # Create a python callback for resources
        RES_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                                     POINTER(Mrp_resource_set),
                                     c_void_p)

        def res_callback_func(res_ctx_p, res_set_p, userdata_p):
            opaque = cast(userdata_p, POINTER(Userdata)).contents.opaque

            passed_conn    = given_reslib_connection(res_ctx_p)
            passed_res_set = given_resource_set(passed_conn, res_set_p)

            # Call the actual higher-level python callback func
            self.res_cb(passed_res_set, opaque)

        self.res_callback = RES_CALLBACKFUNC(res_callback_func)

        self.res_set = \
            mrp_reslib.mrp_res_create_resource_set(conn.res_ctx,
                                                   mrp_class,
                                                   self.res_callback,
                                                   pointer(conn.udata))

        if not self.res_set:
            self.__del__()

    def acquire(self):
        return \
            mrp_reslib.mrp_res_acquire_resource_set(self.conn.res_ctx,
                                                    self.res_set)

    def release(self):
        return \
            mrp_reslib.mrp_res_release_resource_set(self.conn.res_ctx,
                                                    self.res_set)

    def get_id(self):
        return \
            mrp_reslib.mrp_res_get_resource_set_id(self.conn.res_ctx,
                                                   self.res_set)

    def create_resource(self, name, mandatory=True, shared=False):
        res = resource(self.conn, self, name, mandatory, shared)

        return res

    def list_resource_names(self):
        names = []

        mrp_list = \
            mrp_reslib.mrp_res_list_resource_names(self.conn.res_ctx,
                                                   self.res_set).contents

        if mrp_list:
            for i in xrange(mrp_list.num_strings):
                names.append(mrp_list.strings[i])

            mrp_reslib.mrp_res_free_string_array(mrp_list)
            mrp_list = None

        return names

    def get_resource_by_name(self, name):
        resource = None

        mrp_res = \
            mrp_reslib.mrp_res_get_resource_by_name(self.conn.res_ctx,
                                                    self.res_set,
                                                    name)

        if mrp_res:
            resource = given_resource(self, mrp_res)

        return resource

    def delete_resource(self, res):
        return mrp_reslib.mrp_res_delete_resource(self.res_set, res.res)

    def delete_resource_by_name(self, name):
        return mrp_reslib.mrp_res_delete_resource_by_name(self.res_set,
                                                          name)

    def get_state(self):
        return res_state_to_str(self.res_set.contents.state)

    def equals(self, other):
        return mrp_reslib.mrp_res_equal_resource_set(self.res_set,
                                                     other.res_set)

    def set_autorelease(self, status):
        return mrp_reslib.mrp_res_set_autorelease(self.conn.res_ctx,
                                                  status, self.res_set)

    def delete(self):
        mrp_reslib.mrp_res_delete_resource_set(self.conn.res_ctx,
                                               self.res_set)
        self.res_set = None

    # FIXME: I think this might be quite bad,
    #        update the original with the new one until I clean this up
    def _copy(self):
        mrp_res_set = \
            mrp_reslib.mrp_res_copy_resource_set(self.conn.res_ctx,
                                                 self.res_set)
        if mrp_res_set:
            return given_resource_set(self.conn, mrp_res_set)
        else:
            return None

    def update(self, other):
        if self.res_set:
            self.delete()

        mrp_res_set = \
            mrp_reslib.mrp_res_copy_resource_set(other.conn.res_ctx,
                                                 other.res_set)
        if mrp_res_set:
            self.res_set = mrp_res_set
            return True
        else:
            return False


class resource_listing(resource_set):
    def __init__(self, conn):
        self.conn = conn

        self.res_set = \
            mrp_reslib.mrp_res_list_resources(self.conn.res_ctx)

        if not self.res_set:
            self.res_set = None
            self.__del__()


class given_resource_set(resource_set):
    def __init__(self, conn, res_set):
        self.conn = conn
        self.res_set = res_set


class reslib_connection():
    def __init__(self, status_cb, opaque_data):
        self.udata    = Userdata(self, opaque_data)
        self.mainloop = None
        self.res_ctx  = None
        self.status_cb = None
        self.conn_status_callback = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False

        self.status_cb = status_cb

        def conn_status_callback_func(res_ctx_p, error_code, userdata_p):
            self.conn_status_callback_called = True
            conn = given_reslib_connection(res_ctx_p)
            if error_to_str(error_code) == "none" and conn.get_state() == "connected":
                self.connected_to_murphy = True

            opaque = cast(userdata_p, POINTER(Userdata)).contents.opaque

            # Call the actual Python-level callback func
            self.status_cb(conn, error_code, opaque)

        # Create the connection status callback
        CONN_STATUS_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                                             c_uint, c_void_p)
        self.conn_status_callback = \
            CONN_STATUS_CALLBACKFUNC(conn_status_callback_func)

    def connect(self):
        self.mainloop = mrp_common.mrp_mainloop_create()
        if not self.mainloop:
            self.disconnect()
            return False

        self.res_ctx = mrp_reslib.mrp_res_create(self.mainloop,
                                                 self.conn_status_callback,
                                                 pointer(self.udata))
        if not self.res_ctx:
            self.disconnect()
            return False

        while self.iterate():
            if not self.conn_status_callback_called:
                continue
            else:
                connected = self.connected_to_murphy
                if not connected:
                    self.disconnect()

                return connected

    def iterate(self):
        if self.mainloop:
            return mrp_common.mrp_mainloop_iterate(self.mainloop)

    def disconnect(self):
        if self.res_ctx:
            mrp_reslib.mrp_res_destroy(self.res_ctx)

        if self.mainloop:
            mrp_common.mrp_mainloop_quit(self.mainloop, 0)
            mrp_common.mrp_mainloop_destroy(self.mainloop)

    def create_resource_set(self, res_cb, mrp_class):
        return resource_set(res_cb, self, mrp_class)

    def list_application_classes(self):
        class_list = []

        mrp_list = \
            mrp_reslib.mrp_res_list_application_classes(self.res_ctx)

        if mrp_list:
            for i in xrange(mrp_list.contents.num_strings):
                class_list.append(mrp_list.contents.strings[i])

            mrp_list = None

        return class_list

    def list_resources(self):
        return resource_listing(self)

    def get_state(self):
        return conn_state_to_str(self.res_ctx.contents.state)


class given_reslib_connection(reslib_connection):
    def __init__(self, res_ctx):
        self.res_ctx = res_ctx


class status_obj():
    def __init__(self):
        self.connection = None
        self.res_set = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False
        self.res_set_changed         = False
        self.tests_successful        = False


if __name__ == "__main__":
    # Basic statuses
    test_run       = False
    check_run      = False
    test_succeeded = False

    # Create the general status object (passed on as opaque)
    status = status_obj()

    # Create a connection object and try to connect to Murphy
    conn = reslib_connection(py_status_callback, status)
    connected = conn.connect()
    if not connected:
        print("Main: Couldn't connect")
        sys.exit(2)

    # Run the actual changes
    finished_test = actual_test_steps(conn)
    if not finished_test:
        print("Main: Test not finished")
        conn.disconnect()
        sys.exit(3)

    # Check the results of the changes done
    while conn.iterate():
        print("res_set_changed: %s" % (status.res_set_changed))

        if not check_run and status.res_set_changed:
            test_succeeded = check_tests_results(conn)
            check_run = True
            break

    conn.disconnect()

    sys.exit(not (check_run and test_succeeded))
