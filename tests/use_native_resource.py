#!/usr/bin/env python

from os.path import (dirname, realpath)
from ctypes import (Structure, POINTER, pointer, CFUNCTYPE,
                    cast, c_int, c_uint, c_char_p, c_void_p,
                    c_bool, CDLL, py_object)
import threading
import time


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
mrp_resource = CDLL(path + "/../src/.libs/libmurphy-resource.so")


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
                ("event",   py_object)]

# Set the arguments/return value types for used variables
mrp_resource.mrp_res_create.restype = POINTER(Mrp_resource_ctx)

mrp_resource.mrp_res_list_application_classes.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_resource.mrp_res_list_application_classes.restype  = POINTER(Mrp_string_array)

mrp_resource.mrp_res_list_resources.argtypes = [POINTER(Mrp_resource_ctx)]
mrp_resource.mrp_res_list_resources.restype  = POINTER(Mrp_resource_set)

mrp_resource.mrp_res_list_resource_names.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
mrp_resource.mrp_res_list_resource_names.restype  = POINTER(Mrp_string_array)

mrp_resource.mrp_res_create_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                     c_char_p, c_void_p,
                                                     c_void_p]
mrp_resource.mrp_res_create_resource_set.restype  = POINTER(Mrp_resource_set)

mrp_resource.mrp_res_create_resource.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set),
                                                 c_char_p, c_bool, c_bool]
mrp_resource.mrp_res_create_resource.restype  = POINTER(Mrp_resource)

mrp_resource.mrp_res_acquire_resource_set.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
mrp_resource.mrp_res_acquire_resource_set.restype  = c_int

mrp_resource.mrp_res_equal_resource_set.argtypes = [POINTER(Mrp_resource_set),
                                                    POINTER(Mrp_resource_set)]
mrp_resource.mrp_res_equal_resource_set.restype  = c_bool

mrp_resource.mrp_res_get_resource_by_name.argtypes = [POINTER(Mrp_resource_ctx),
                                                      POINTER(Mrp_resource_set),
                                                      c_char_p]
mrp_resource.mrp_res_get_resource_by_name.restype  = POINTER(Mrp_resource)

# Create the resource context callback
RES_CTX_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                                 c_uint, c_void_p)


def res_ctx_callback_func(res_ctx_p, error_code, userdata):
    res_ctx     = res_ctx_p.contents
    app_classes = None

    if res_ctx.state == MRP_RES_CONNECTED:
        print("We are connected!\n")

        print("Infodump:\n")

        # Let's try getting the classes
        app_classes = mrp_resource.mrp_res_list_application_classes(res_ctx_p)

        if app_classes:
            for i in xrange(app_classes.contents.num_strings):
                print('Class %d: %s' % (i, app_classes.contents.strings[i]))

        # Let's try getting all the resources
        res_set = mrp_resource.mrp_res_list_resources(res_ctx_p)

        if res_set:
            res_names = mrp_resource.mrp_res_list_resource_names(res_ctx_p,
                                                                 res_set)

            if res_names:
                for i in xrange(res_names.contents.num_strings):
                    print('Resource %d: %s' % (i, res_names.contents.strings[i]))

    print('ResCtxCallback ErrCode: %d' % (error_code))
    return

res_ctx_callback = RES_CTX_CALLBACKFUNC(res_ctx_callback_func)


# Define a thread for the Murphy mainloop
class mainLoopThread(threading.Thread):
    def __init__(self, threadID, name, ml):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name     = name
        self.mainloop = ml

    def run(self):
        mrp_common.mrp_mainloop_run(mainloop)

# Create a python callback for resources
RES_CALLBACKFUNC = CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                             POINTER(Mrp_resource_set),
                             c_void_p)


def res_callback_func(res_ctx_p, res_set_p, userdata_p):
    print("ResCallBack: Entered")

    userdata = cast(userdata_p, POINTER(Userdata)).contents

    if not mrp_resource.mrp_res_equal_resource_set(res_set_p, userdata.res_set):
        print("ResCallBack: Resource sets are not equal")
        return

    print("ResCallBack: Resource set is: %s" % (res_state_to_str(res_set_p.contents.state)))

    checked_resource = mrp_resource.mrp_res_get_resource_by_name(res_ctx_p,
                                                                 res_set_p,
                                                                 "audio_playback")

    if checked_resource:
        print("ResCallBack: Resouce 'audio playback' is: %s" % (res_state_to_str(checked_resource.contents.state)))

res_callback = RES_CALLBACKFUNC(res_callback_func)


# First test
def first_test(udata):
    # Create a clean, empty new resource set
    udata.res_set = mrp_resource.mrp_res_create_resource_set(udata.ctx,
                                                             "player",
                                                             res_callback,
                                                             pointer(udata))

    if not udata.res_set:
        print("Failed to create a resource set")
        return

    # Add the audio_playback resource to the empty set
    resource = mrp_resource.mrp_res_create_resource(udata.ctx,
                                                    udata.res_set,
                                                    "audio_playback",
                                                    True, False)

    if not resource:
        print("Can has no resource")
        return

    acquired_status = mrp_resource.mrp_res_acquire_resource_set(udata.ctx,
                                                                udata.res_set)

    print('FirstTest acquired status: %d' % (acquired_status))

    time.sleep(10)


if __name__ == "__main__":
    udata = Userdata(None, None, None)

    # Create a mainloop since the resource API needs one
    mainloop = mrp_common.mrp_mainloop_create()

    # Create the resource context
    udata.ctx = mrp_resource.mrp_res_create(mainloop, res_ctx_callback,
                                            pointer(udata))

    # Set up a second thread for the mainloop
    mainloop_thread = mainLoopThread(1, "mrp_mainloop_thread", mainloop)
    mainloop_thread.start()

    # FIXME: A hack to try and make sure mainloop_thread has gotten somewhere
    time.sleep(0.1)

    first_test(udata)

    print(udata.ctx)
