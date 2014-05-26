#!/usr/bin/env python

import ctypes
import os
import generated_stuff

# FIXME: This fails if run in an interpreter (since __file__ is not available)
path = os.path.dirname(os.path.realpath(__file__))

# Load the murphy resource API library as well as the common library
libmurphy_common   = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-common.so")
libmurphy_resource = ctypes.cdll.LoadLibrary(path + "/../src/.libs/libmurphy-resource.so")

mainloop = libmurphy_common.mrp_mainloop_create()

ctx = libmurphy_resource.mrp_res_create(mainloop,)
