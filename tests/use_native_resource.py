#!/usr/bin/env python

from os.path import (dirname, realpath)
from ctypes import (Structure, POINTER, pointer, CFUNCTYPE,
                    cast, c_int, c_uint, c_char_p, c_void_p,
                    c_bool, CDLL, py_object)
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

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = dirname(realpath(__file__))

# Load the murphy resource API library as well as the common library
mrp_common = CDLL(path + "/../src/.libs/libmurphy-common.so")
mrp_reslib = CDLL(path + "/../src/.libs/libmurphy-resource.so")


# Create general abstractions around the things we throw around
class Mrp_mainloop(Structure):
    pass


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


class Userdata(Structure):
    _fields_ = [("ctx",     POINTER(Mrp_resource_ctx)),
                ("res_set", POINTER(Mrp_resource_set)),
                ("py_obj",  py_object)]

# Set the arguments/return value types for used variables
mrp_reslib.mrp_res_create.restype = POINTER(Mrp_resource_ctx)

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

mrp_reslib.mrp_res_create_resource.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set),
                                               c_char_p, c_bool, c_bool]
mrp_reslib.mrp_res_create_resource.restype  = POINTER(Mrp_resource)

mrp_reslib.mrp_res_acquire_resource_set.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_acquire_resource_set.restype  = c_int

mrp_reslib.mrp_res_equal_resource_set.argtypes = [POINTER(Mrp_resource_set),
                                                  POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_equal_resource_set.restype  = c_bool

mrp_reslib.mrp_res_get_resource_by_name.argtypes = [POINTER(Mrp_resource_ctx),
                                                    POINTER(Mrp_resource_set),
                                                    c_char_p]
mrp_reslib.mrp_res_get_resource_by_name.restype  = POINTER(Mrp_resource)

mrp_reslib.mrp_res_destroy.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_reslib.mrp_res_destroy.restype  = None

mrp_reslib.mrp_res_delete_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                   POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_delete_resource_set.restype  = None

mrp_reslib.mrp_res_copy_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                 POINTER(Mrp_resource_set)]
mrp_reslib.mrp_res_copy_resource_set.restype  = POINTER(Mrp_resource_set)

mrp_common.mrp_mainloop_destroy.restype = None


# Create the resource context callback
RES_CTX_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                                 c_uint, c_void_p)


def res_ctx_callback_func(res_ctx_p, error_code, userdata_p):
    res_ctx     = res_ctx_p.contents
    app_classes = None

    status = cast(userdata_p, POINTER(Userdata)).contents.py_obj
    status.res_ctx_callback_called = True

    if res_ctx.state == MRP_RES_CONNECTED:
        print("We are connected!\n")

        print("Infodump:\n")

        # Let's try getting the classes
        app_classes = mrp_reslib.mrp_res_list_application_classes(res_ctx_p)

        if app_classes:
            for i in xrange(app_classes.contents.num_strings):
                print('Class %d: %s' % (i, app_classes.contents.strings[i]))

        # Let's try getting all the resources
        res_set = mrp_reslib.mrp_res_list_resources(res_ctx_p)

        if res_set:
            res_names = mrp_reslib.mrp_res_list_resource_names(res_ctx_p,
                                                               res_set)

            if res_names:
                for i in xrange(res_names.contents.num_strings):
                    print('Resource %d: %s' % (i, res_names.contents.strings[i]))

        status.connected_to_murphy = True
    else:
        status.connected_to_murphy = False

    print('ResCtxCallback ErrCode: %d' % (error_code))
    return

res_ctx_callback = RES_CTX_CALLBACKFUNC(res_ctx_callback_func)


# Create a python callback for resources
RES_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                             POINTER(Mrp_resource_set),
                             c_void_p)


def res_callback_func(res_ctx_p, res_set_p, userdata_p):
    print("ResCallBack: Entered")

    userdata = cast(userdata_p, POINTER(Userdata)).contents

    # Check if this callback is for the resource set we have in userdata
    if not mrp_reslib.mrp_res_equal_resource_set(res_set_p, userdata.res_set):
        print("ResCallBack: Callback not for carried userdata")
        return

    print("ResCallBack: Prev status -> " + res_state_to_str(userdata.res_set.contents.state))

    # Print information about the new resource set state
    print("ResCallBack: Resource set is: %s" %
          (res_state_to_str(res_set_p.contents.state)))

    # Print information about the resource itself
    checked_resource = mrp_reslib.mrp_res_get_resource_by_name(res_ctx_p,
                                                               res_set_p,
                                                               "audio_playback")

    if checked_resource:
        print("ResCallBack: Resouce 'audio playback' is: %s" %
              (res_state_to_str(checked_resource.contents.state)))

    # Remove and switch the userdata resource set to a new one
    mrp_reslib.mrp_res_delete_resource_set(res_ctx_p, userdata.res_set)
    userdata.res_set = mrp_reslib.mrp_res_copy_resource_set(res_ctx_p,
                                                            res_set_p)

    userdata.py_obj.res_set_changed = True

res_callback = RES_CALLBACKFUNC(res_callback_func)


def actual_test_steps(udata):
    connection = udata.py_obj.connection
    # Create a clean, empty new resource set
    res_set = connection.create_resource_set("player")
    if not res_set:
        print("Failed to create a resource set")
        return False

    udata.res_set = res_set.res_set

    # Add the audio_playback resource to the empty set
    resource = res_set.create_resource("audio_playback").res
    if not resource:
        print("Can has no resource")
        return False

    acquired_status = res_set.acquire()

    return not acquired_status


def check_tests_results(udata):
    # Check new status
    if udata.res_set.contents.state != MRP_RES_RESOURCE_ACQUIRED:
        print("FirstTest: Something went wrong, resource set's not ours")
        return False
    else:
        print("FirstTest: Yay, checked that we now own the resource")
        return True


class resource():
    def __init__(self, conn, res_set, name, mandatory=True, shared=False):
        self.res = \
            mrp_reslib.mrp_res_create_resource(conn.udata.ctx,
                                               res_set.res_set,
                                               name, mandatory,
                                               shared)


class resource_set():
    def __init__(self, conn, mrp_class):
        self.connection = conn
        self.mrp_class  = mrp_class

        self.res_set = \
            mrp_reslib.mrp_res_create_resource_set(conn.udata.ctx,
                                                   mrp_class,
                                                   res_callback,
                                                   pointer(conn.udata))

        if not self.res_set:
            __del__(self)

    def acquire(self):
        return \
            mrp_reslib.mrp_res_acquire_resource_set(self.connection.udata.ctx,
                                                    self.res_set)

    def create_resource(self, name, mandatory=True, shared=False):
        return resource(self.connection, self, name, mandatory, shared)


class reslib_connection():
    def __init__(self, udata):
        self.udata    = udata
        self.mainloop = None

        self.udata.py_obj.connection = self

    def connect(self):
        status = self.udata.py_obj

        self.mainloop = mrp_common.mrp_mainloop_create()
        if not self.mainloop:
            self.disconnect()
            return False

        self.udata.ctx = mrp_reslib.mrp_res_create(self.mainloop,
                                                   res_ctx_callback,
                                                   pointer(udata))
        if not self.udata.ctx:
            self.disconnect()
            return False

        while mrp_common.mrp_mainloop_iterate(self.mainloop):
            if not status.res_ctx_callback_called:
                continue
            else:
                connected = status.connected_to_murphy
                if not connected:
                    self.disconnect()

                return connected

    def iterate(self):
        if self.mainloop:
            return mrp_common.mrp_mainloop_iterate(self.mainloop)

    def disconnect(self):
        if self.udata.ctx:
            mrp_reslib.mrp_res_destroy(self.udata.ctx)

        if self.mainloop:
            mrp_common.mrp_mainloop_quit(self.mainloop, 0)
            mrp_common.mrp_mainloop_destroy(self.mainloop)

    def create_resource_set(self, mrp_class):
        return resource_set(self, mrp_class)


class status_obj():
    def __init__(self):
        self.connection = None

        self.res_ctx_callback_called = False
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
    udata = Userdata(None, None, status)

    # Create a connection object and try to connect to Murphy
    connection = reslib_connection(udata)
    connected = connection.connect()
    if not connected:
        print("Main: Couldn't connect")
        sys.exit(2)

    # Run the actual changes
    finished_test = actual_test_steps(udata)
    if not finished_test:
        print("Main: Test not finished")
        connection.disconnect()
        sys.exit(3)

    # Check the results of the changes done
    while connection.iterate():
        print("res_set_changed: %s" % (status.res_set_changed))

        if not check_run and status.res_set_changed:
            test_succeeded = check_tests_results(udata)
            check_run = True
            break

    connection.disconnect()

    sys.exit(not (check_run and test_succeeded))
