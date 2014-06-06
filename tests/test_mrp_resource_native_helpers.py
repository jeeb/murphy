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

def py_status_callback(conn, error_code, opaque):
    if conn.get_state() == "connected":
        print("StatusCallback: We are connected!")

        print("StatusCallBack: Infodump:\n")

        # Let's try getting the classes
        app_classes = conn.list_application_classes()

        for app_class in app_classes:
            print('Class: %s' % (app_class))

        # Let's try getting all the resources
        res_set = conn.list_resources()
        res_names = res_set.list_resource_names()

        for name in res_names:
            res = res_set.get_resource_by_name(name)
            attr_list = res.list_attribute_names()

            print('Resource: %s' % (name))
            for attr_name in attr_list:
                attr = res.get_attribute_by_name(attr_name)
                print("\tAttribute: %s = %s" % (attr_name, attr.get_value()))

    print('StatusCallback ErrCode: %d\n' % (error_code))


def py_res_callback(new_res_set, opaque):
    print("ResCallBack: Entered")

    # Get the old res set from the opaque data
    res_set = opaque.res_set

    # Check if this callback is for the resource set we have in userdata
    if not new_res_set:
        print("ResCallBack: No resource set yet set")
        return
    elif not res_set.equals(new_res_set):
        print("ResCallBack: Callback not for carried resource set")
        return

    state = StateDump(res_set)
    new_state = StateDump(new_res_set)

    if new_state.equals(state):
        print("ResCallBack: Resource set contents identical")
    else:
        print("ResCallBack: Resource set contents changed")
        opaque.res_set_changed = True
        state.print_differences(new_state)

    # Remove and switch the userdata resource set to a new one
    res_set.update(new_res_set)

    print("ResCallBack: Exited\n")


def create_res_set(conn, callback):
        conn.get_opaque_data().res_set = conn.create_resource_set(callback, "player")
        conn.get_opaque_data().res_set.create_resource("audio_playback")

        # Create two state dumps of our resource set for current/expected state
        conn.get_opaque_data().res_set_state = StateDump(conn.get_opaque_data().res_set)
        conn.get_opaque_data().res_set_expected_state = StateDump(conn.get_opaque_data().res_set)


def py_grab_resource_set(conn, callback):
    # Create a resource set in case it doesn't exist
    if not conn.get_opaque_data().res_set:
        create_res_set(conn, callback)

    state = conn.get_opaque_data().res_set_state
    res_set = conn.get_opaque_data().res_set

    if res_set.get_state() != "acquired":
        state.set_acquired()
        return not res_set.acquire()
    else:
        return True


def py_modify_attribute(conn, callback, name, value):
    status = conn.get_opaque_data()

    # Create a resource set in case it doesn't exist
    if not status.res_set:
        create_res_set(conn, callback)

    # Bring the current res_set into local scope
    res_set = status.res_set

    # Update the current res_set state dump
    status.res_set_state = StateDump(res_set)
    state = status.res_set_state

    # Do the simulated change to it
    state.resources["audio_playback"].attributes[name].value = value

    # Actually do the change
    result = res_set.get_resource_by_name("audio_playback").get_attribute_by_name(name).set_value_to(value)

    if result:
        return False

    if res_set.get_state() != "acquired":
        state.set_acquired()
        return not res_set.acquire()
    else:
        return True


def py_check_result(conn):
    res_set = conn.get_opaque_data().res_set

    desired_state = conn.get_opaque_data().res_set_state

    curr_state = StateDump(res_set)

    if not desired_state.equals(curr_state):
        print("CheckResult: State did not meet expectations!\n")
        desired_state.print_differences(curr_state)
        return False
    else:
        print("CheckResult: State met expectations!\n")
        return True


class StatusObj():
    def __init__(self):
        self.res_set = None

        self.res_set_state = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False
        self.res_set_changed         = False
        self.tests_successful        = False


class StateDumpAttribute(object):
    def __init__(self, attr):
        self.name  = attr.get_name()
        self.value = attr.get_value()

    def equals(self, other):
        return self.name == other.name and self.value == other.value

    def print_differences(self, other):
        if self.value != other.value:
            print("\t\tAttribute %s: %s != %s" % (self.name, self.value, other.value))


class StateDumpResource(object):
    def __init__(self, res):
        self.name = res.get_name()
        self.state = res.get_state()
        self.names        = []
        self.attr_objects = []

        for name in res.list_attribute_names():
            self.names.append(name)
            self.attr_objects.append(StateDumpAttribute(res.get_attribute_by_name(name)))

        self.attributes = dict(zip(self.names, self.attr_objects))

    def equals(self, other):
        for attr in self.attr_objects:
            if not attr.equals(other.attributes[attr.name]):
                return False

        return self.state == other.state

    def print_differences(self, other):
        print("\tResource %s:" % (self.name))
        if self.state != other.state:
            print("\t\tState: %s != %s" % (self.state, other.state))

        for attr in self.attr_objects:
            attr.print_differences(other.attributes[attr.name])


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
