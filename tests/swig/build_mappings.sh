#!/usr/bin/env bash

swig -v -Wall -Wextra -python -I../.. mrp_resource_api.i

gcc -Wall -Wextra -shared -fPIC -o _mrp_resource_api.so -I/usr/include/python2.7 -I../.. -I../../src/plugins/resource-native/libmurphy-resource mrp_resource_api_wrap.c -L../../src/.libs -lmurphy-resource -lmurphy-common
