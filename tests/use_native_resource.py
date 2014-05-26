#!/usr/bin/env python

import ctypes
import os

# Pick something to generate these things in the future
(MRP_RES_CONNECTED, MRP_RES_DISCONNECTED) = (0,1)
(MRP_RES_RESOURCE_LOST, MRP_RES_RESOURCE_PENDING, MRP_RES_RESOURCE_ACQUIRED, MRP_RES_RESOURCE_AVAILABLE) = (0,1,2,3)
(MRP_RES_ERROR_NONE, MRP_RES_ERROR_CONNECTION_LOST, MRP_RES_ERROR_INTERNAL, MRP_RES_ERROR_MALFORMED) = (0,1,2,3)

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = os.path.dirname(os.path.realpath(__file__))

# Load the murphy resource API library as well as the common library
libmurphy_common   = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-common.so")
libmurphy_resource = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-resource.so")

# Create general abstractions around the things we throw around
class mrp_mainloop(ctypes.Structure):
    # _fields_ = []
    pass

class mrp_resource_ctx(ctypes.Structure):
    _fields_ = [("state", ctypes.c_uint),
                ("zone", ctypes.c_char_p),
                ("priv", ctypes.c_void_p)]

# Create a python callback function that we will then proceed to
# stick into SWIG, if possible
CALLBACKFUNC = ctypes.CFUNCTYPE(None, ctypes.POINTER(mrp_resource_ctx),
                                ctypes.POINTER(ctypes.c_int), ctypes.c_void_p)
def py_callback_func(res_ctx, error_msg, userdata):
    print("Wunderbar!")
    return

callback_func = CALLBACKFUNC(py_callback_func)

class mrp_resource_set(ctypes.Structure):
    _fields_ = [("application_class", ctypes.c_char_p),
                ("state", ctypes.c_void_p),  # mrp_resource_state_t
                ("priv", ctypes.c_void_p)]

class userdata(ctypes.Structure):
    _fields_ = [("ctx",     ctypes.POINTER(mrp_resource_ctx)),
                ("res_set", ctypes.POINTER(mrp_resource_set))]

if __name__ == "__main__":
    # Create a mainloop since the resource API needs one
    mainloop = libmurphy_common.mrp_mainloop_create()

    # Create the resource context
    resource_ctx = libmurphy_resource.mrp_res_create(mainloop, callback_func, 0)

    print(mainloop)
    print(libmurphy_resource)
