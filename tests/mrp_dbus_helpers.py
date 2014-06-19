#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class StateDumpResource(object):
    def __init__(self, res):
        self.name = res.get_name()
        self.state = res.get_state()
        self.attr_names  = []
        self.attr_values = []

        for name in res.list_attribute_names():
            self.attr_names.append(name)
            self.attr_values.append(res.get_attribute_value(name))

        self.attributes = dict(zip(self.attr_names, self.attr_values))

    def equals(self, other):
        # If we have a different amount of attributes we definitely aren't dealing with the same thing
        if len(other.attr_names) != len(self.attr_names):
            return False

        # If one of the values is not the same, we stop at that and return False
        for name in self.attr_names:
            if self.attributes[name] != other.attributes[name]:
                return False

        # And finally there's the state
        return self.state == other.state

    def print_differences(self, other):
        print("\tResource %s:" % (self.name))
        if self.state != other.state:
            print("\t\tState: %s != %s" % (self.state, other.state))

        for name in self.attr_names:
            if self.attributes[name] != other.attributes[name]:
                print("\t\tAttribute %s: %s != %s" % (name, self.attributes[name], other.attributes[name]))


class StateDump(object):
    def __init__(self, res_set):
        self.names       = []
        self.res_objects = []
        self.state = res_set.get_state()

        for name in res_set.list_resource_names():
            self.names.append(name)
            self.res_objects.append(StateDumpResource(res_set.get_resource_by_name(name)))

        self.resources = dict(zip(self.names, self.res_objects))

    def equals(self, other):
        for res in self.res_objects:
            if not res.equals(other.resources[res.name]):
                return False

        return self.state == other.state

    def print_differences(self, other):
        print("Resource Set:")
        if self.state != other.state:
            print("\tState: %s != %s" % (self.state, other.state))

        for res in self.res_objects:
            res.print_differences(other.resources[res.name])

    def set_acquired(self):
        self.state = "acquired"
        for res in self.resources.itervalues():
            res.state = "acquired"
