#!/usr/bin/env python

from ctypes import POINTER
import ctypes
import os
import threading
import time


# Murphy resource-native API related statuses
(MRP_RES_CONNECTED, MRP_RES_DISCONNECTED) = (0,1)
(MRP_RES_RESOURCE_LOST, MRP_RES_RESOURCE_PENDING, MRP_RES_RESOURCE_ACQUIRED, MRP_RES_RESOURCE_AVAILABLE) = (0,1,2,3)
(MRP_RES_ERROR_NONE, MRP_RES_ERROR_CONNECTION_LOST, MRP_RES_ERROR_INTERNAL, MRP_RES_ERROR_MALFORMED) = (0,1,2,3)

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = os.path.dirname(os.path.realpath(__file__))

# Load the murphy resource API library as well as the common library
libmurphy_common   = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-common.so")
libmurphy_resource = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-resource.so")


# Create general abstractions around the things we throw around
class Mrp_mainloop(ctypes.Structure):
    pass


class Mrp_resource_ctx(ctypes.Structure):
    _fields_ = [("state", ctypes.c_uint),
                ("zone",  ctypes.c_char_p),
                ("priv",  ctypes.c_void_p)]


class Mrp_resource_set(ctypes.Structure):
    _fields_ = [("application_class", ctypes.c_char_p),
                ("state",             ctypes.c_uint),
                ("priv",              ctypes.c_void_p)]


class Mrp_string_array(ctypes.Structure):
    _fields_ = [("num_strings", ctypes.c_int),
                ("strings",     POINTER(ctypes.c_char_p))]


class Mrp_resource(ctypes.Structure):
    _fields_ = [("name",  ctypes.c_char_p),
                ("state", ctypes.c_uint),
                ("priv",  ctypes.c_void_p)]


class Userdata(ctypes.Structure):
    _fields_ = [("ctx",     POINTER(Mrp_resource_ctx)),
                ("res_set", POINTER(Mrp_resource_set))]

# Set the arguments/return value types for used variables
libmurphy_resource.mrp_res_create.restype = POINTER(Mrp_resource_ctx)

libmurphy_resource.mrp_res_list_application_classes.argtypes = [POINTER(Mrp_resource_ctx)]
libmurphy_resource.mrp_res_list_application_classes.restype  = POINTER(Mrp_string_array)

libmurphy_resource.mrp_res_list_resources.argtypes = [POINTER(Mrp_resource_ctx)]
libmurphy_resource.mrp_res_list_resources.restype  = POINTER(Mrp_resource_set)

libmurphy_resource.mrp_res_list_resource_names.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
libmurphy_resource.mrp_res_list_resource_names.restype  = POINTER(Mrp_string_array)

libmurphy_resource.mrp_res_create_resource_set.argtypes = [POINTER(Mrp_resource_ctx),
                                                           ctypes.c_char_p, ctypes.c_void_p,
                                                           ctypes.c_void_p]
libmurphy_resource.mrp_res_create_resource_set.restype  = POINTER(Mrp_resource_set)

libmurphy_resource.mrp_res_create_resource.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set),
                                                       ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool]
libmurphy_resource.mrp_res_create_resource.restype  = POINTER(Mrp_resource)

libmurphy_resource.mrp_res_acquire_resource_set.argtypes = [POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set)]
libmurphy_resource.mrp_res_acquire_resource_set.restype  = ctypes.c_int

libmurphy_resource.mrp_res_equal_resource_set.argtypes = [POINTER(Mrp_resource_set),
                                                          POINTER(Mrp_resource_set)]
libmurphy_resource.mrp_res_equal_resource_set.restype  = ctypes.c_bool

# Create the resource context callback
RES_CTX_CALLBACKFUNC = ctypes.CFUNCTYPE(None, POINTER(Mrp_resource_ctx),
                                        ctypes.c_uint, ctypes.c_void_p)
def res_ctx_callback_func(res_ctx_p, error_code, userdata):
    res_ctx     = res_ctx_p.contents
    app_classes = None

    if res_ctx.state == MRP_RES_CONNECTED:
        print("We are connected!\n")

        print("Infodump:\n")

        # Let's try getting the classes
        app_classes = libmurphy_resource.mrp_res_list_application_classes(res_ctx_p)

        if app_classes:
            for i in xrange(app_classes.contents.num_strings):
                print('Class %d: %s' % (i, app_classes.contents.strings[i]))

        # Let's try getting all the resources
        res_set = libmurphy_resource.mrp_res_list_resources(res_ctx_p)

        if res_set:
            res_names = libmurphy_resource.mrp_res_list_resource_names(res_ctx_p, res_set)

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
        libmurphy_common.mrp_mainloop_run(mainloop)


# Create a python callback for resources
RES_CALLBACKFUNC = ctypes.CFUNCTYPE(None, POINTER(Mrp_resource_ctx), POINTER(Mrp_resource_set),
                                    ctypes.c_void_p)


def res_callback_func(res_ctx_p, res_set_p, userdata):
    udata = ctypes.cast(userdata, Userdata)

    if mrp_res_equal_resource_set(res_set, udata.res_set):
        print("ResCallBack: Them resource sets are equal")
    else:
        print("ResCallBack: Them resource sets are not equal")

    return

res_callback = RES_CALLBACKFUNC(res_callback_func)


# First test
def first_test(udata):
    # Create a clean, empty new resource set
    udata.res_set = libmurphy_resource.mrp_res_create_resource_set(udata.ctx, 'player', res_callback, ctypes.pointer(udata))

    if not udata.res_set:
        print("Failed to create a resource set")
        return

    # Add the audio_playback resource to the empty set
    resource = libmurphy_resource.mrp_res_create_resource(udata.ctx, udata.res_set, 'audio_playback',
                                                          True, False)

    if not resource:
        print("Can has no resource")
        return

    acquired_status = libmurphy_resource.mrp_res_acquire_resource_set(udata.ctx, udata.res_set)

    print('FirstTest acquired status: %d' % (acquired_status))

    time.sleep(2)


if __name__ == "__main__":
    udata = Userdata(None, None)

    # Create a mainloop since the resource API needs one
    mainloop = libmurphy_common.mrp_mainloop_create()

    # Create the resource context
    udata.ctx = libmurphy_resource.mrp_res_create(mainloop, res_ctx_callback, udata)

    # Set up a second thread for the mainloop
    mainloop_thread = mainLoopThread(1, "mrp_mainloop_thread", mainloop)
    mainloop_thread.start()

    # FIXME: A hack to try and make sure mainloop_thread has gotten somewhere
    time.sleep(0.1)

    first_test(udata)

    print(udata.ctx)
