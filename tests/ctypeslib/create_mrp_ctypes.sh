#!/usr/bin/env bash

h2xml murphy/plugins/resource-native/libmurphy-resource/resource-api.h -I ../.. -c -o xml_output.xml

xml2py xml_output.xml -r mrp_.* > generated_stuff.py
