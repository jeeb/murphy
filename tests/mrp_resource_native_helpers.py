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


def get_test_value_by_type(type):
    """
    Returns a value meant for testing of a given Murphy attribute type

    :param type: Murphy attribute type given as a single-character string
    :return:     A valid value that can be used for testing of an attribute
    """
    return {
        "s": "testString",
        "i": -9001,
        "u": 1192,
        "f": 3.14,
    }.get(type)


def new_res_callback(new_res_set, opaque):
    """
    Example resource set status callback implementation

    :param new_res_set: Current state of a resource set registered for this callback
                        function as a ResourceSet object.
    :param opaque:      Undefined "user data" object, which one sets when registering
                        the callback. This example implementation requires it to be an
                        instance of StatusObj
    :return:            Void
    """
    print("ResCallBack: Entered")

    # Get the current res set from the opaque data
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


def check_results(conn):
    """
    Example function used in testing; Iterates until the updated resource set is as
    saved in a StateDump instance contained in the opaque "user data"

    :param conn: Connection instance
    :return:     Void
    """
    while conn.iterate():
        print("Iterated: res_set_changed = %s" % (conn.get_opaque_data().res_set_changed))
        if conn.get_opaque_data().res_set_changed:
            if py_check_result(conn):
                return


def py_check_result(conn):
    """
    Example function used in testing; Compares the state of the resource set saved in the opaque
    "user data" against a StateDump also contained in it

    :param conn: Connection instance
    :return:     False if the StateDump and the resource set differ in state, True
                 otherwise
    """
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


def update_state_dumps(conn, res_set):
    """
    Updates the state dumps kept in the opaque user data
    """
    if not res_set:
        conn.get_opaque_data().res_set_state          = None
        conn.get_opaque_data().res_set_expected_state = None
    else:
        conn.get_opaque_data().res_set_state          = StateDump(res_set)
        conn.get_opaque_data().res_set_expected_state = StateDump(res_set)


def py_status_callback(conn, error_code, opaque):
    """
    Example connection status callback implementation

    :param conn:       Connection object for which this callback was executed
    :param error_code: Murphy error code given for this connection
    :param opaque:     Undefined "user data" object, which one sets when
                       registering the callback. Not used in this example
                       implementation.
    :return:           Void
    """
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
                if attr:
                    print("\tAttribute: %s = %s" % (attr_name, attr.get_value()))

    print('StatusCallback ErrCode: %s\n' % (error_code))


class StatusObj():
    """
    Example object that can be used as the opaque "user data" in callbacks
    """
    def __init__(self):
        self.res_set = None

        self.res_set_state = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False
        self.res_set_changed         = False
        self.tests_successful        = False


class StateDumpAttribute(object):
    def __init__(self, attr):
        """
        Creates a dump of the state of an attribute

        :param attr: Attribute object to be dumped
        :return:     Void
        """
        self.name  = attr.get_name()
        self.value = attr.get_value()

    def equals(self, other):
        """
        Checks if the state of this dump equals the state of another

        :param other: StateDumpAttribute object to compare against
        :return:      False if the two states are not equal, True
                      otherwise
        """
        return self.name == other.name and self.value == other.value

    def print_differences(self, other):
        """
        Prints the differences between this state dump and another

        :param other: StateDumpAttribute object to show differences against
        :return:      Void
        """
        if self.value != other.value:
            print("\t\tAttribute %s: %s != %s" % (self.name, self.value, other.value))


class StateDumpResource(object):
    def __init__(self, res):
        """
        Creates a dump of the state of a resource

        :param res: Resource object to be dumped
        :return:    Void
        """
        self.name = res.get_name()
        self.state = res.get_state()
        self.names        = []
        self.attr_objects = []

        for name in res.list_attribute_names():
            self.names.append(name)
            self.attr_objects.append(StateDumpAttribute(res.get_attribute_by_name(name)))

        self.attributes = dict(zip(self.names, self.attr_objects))

    def equals(self, other):
        """
        Checks if the state of this dump equals the state of another

        :param other: StateDumpResource object to compare against
        :return:      False if the two states are not equal, True
                      otherwise
        """
        for attr in self.attr_objects:
            if not attr.equals(other.attributes[attr.name]):
                return False

        return self.state == other.state

    def print_differences(self, other):
        """
        Prints the differences between this state dump and another

        :param other: StateDumpResource object to show differences against
        :return:      Void
        """
        print("\tResource %s:" % (self.name))
        if self.state != other.state:
            print("\t\tState: %s != %s" % (self.state, other.state))

        for attr in self.attr_objects:
            attr.print_differences(other.attributes[attr.name])


class StateDump(object):
    def __init__(self, res_set):
        """
        Creates a dump of the state of a resource set

        :param res_set: ResourceSet object to be dumped
        :return:        Void
        """
        self.names       = []
        self.res_objects = []
        self.state = res_set.get_state()
        self.app_class = res_set.res_set.application_class

        for name in res_set.list_resource_names():
            self.names.append(name)
            self.res_objects.append(StateDumpResource(res_set.get_resource_by_name(name)))

        self.resources = dict(zip(self.names, self.res_objects))

    def equals(self, other):
        """
        Checks if the state of this dump equals the state of another

        :param other: StateDump object to compare against
        :return:      False if the two states are not equal, True
                      otherwise
        """
        for res in self.res_objects:
            if not res.equals(other.resources[res.name]):
                return False

        return self.state == other.state and self.app_class == other.app_class

    def print_differences(self, other):
        """
        Prints the differences between this state dump and another

        :param other: StateDump object to show differences against
        :return:      Void
        """
        print("Resource Set:")
        if self.state != other.state:
            print("\tState: %s != %s" % (self.state, other.state))

        if self.app_class != other.app_class:
            print("\tClass: %s != %s" % (self.app_class, other.app_class))

        for res in self.res_objects:
            res.print_differences(other.resources[res.name])

    def set_acquired(self):
        """
        Sets the values in this state dump's set as well as resources
        to values that match a fully acquired entity

        :return: Void
        """
        self.state = "acquired"
        for res in self.resources.itervalues():
            res.state = "acquired"

    def set_released(self):
        """
        Sets the values in this state dump's set as well as resources
        to values that match a fully released entity

        :return: Void
        """
        self.state = "available"
        for res in self.resources.itervalues():
            res.state = "lost"
