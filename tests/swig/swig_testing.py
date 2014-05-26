#!/usr/bin/env python

import ctypes
import os

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = os.path.dirname(os.path.realpath(__file__))

# Kind of a hack: Load the murphy resource API library as well as
# the common library here in order to not need LD_LIBRARY_PATH poking
libmurphy_common   = ctypes.cdll.LoadLibrary(path + "/../../src/.libs/libmurphy-common.so")
libmurphy_resource = ctypes.cdll.LoadLibrary(path + "/../../src/.libs/libmurphy-resource.so")

# Now we import the actual SWIG mapping
from mrp_resource_api import (
    mrp_mainloop_create,
    mrp_mainloop_destroy,
    mrp_res_create,
    mrp_res_destroy
)

import mrp_resource_api

# Create a python callback function that we will then proceed to
# stick into SWIG, if possible
CALLBACKFUNC = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
                                ctypes.c_void_p)
def py_callback_func(res_ctx, error_msg, userdata):
    print("Wunderbar!")
    return

callback_func = CALLBACKFUNC(py_callback_func)

# General IPC init
def connect():
    ml = mrp_mainloop_create()
    ctx = mrp_res_create(ml, None, None)

    return (ml, ctx)

# Disconnect and destroy related contexts
def disconnect(ml, ctx):
    mrp_res_destroy(ctx)
    mrp_mainloop_destroy(ml)

cfunc = mrp_resource_api.mrp_res_state_callback_t()

# Start it up!
ml = mrp_mainloop_create()
ctx = mrp_res_create(ml, callback_func, None)


# Shut it down!
# disconnect(ml, ctx)
