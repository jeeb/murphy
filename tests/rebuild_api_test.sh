#!/usr/bin/env bash

gcc -Wall -Wextra -o ../src/api_test -I.. -L../src/.libs ../src/plugins/resource-native/libmurphy-resource/api_test.c -lmurphy-common -lmurphy-resource
