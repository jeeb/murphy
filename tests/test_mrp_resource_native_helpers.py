#!/usr/bin/env python
# -*- coding: utf-8 -*-

def py_status_callback(conn, error_code, opaque):
    if conn.get_state() == "connected":
        print("We are connected!\n")

        print("Infodump:\n")

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

    print('ResCtxCallback ErrCode: %d' % (error_code))

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

    # Print information about the old resource set state
    print("ResCallBack: Previously resource set was: %s" %
          (res_set.get_state()))

    # Print information about the new resource set state
    print("ResCallBack: Resource set now is: %s" %
          (new_res_set.get_state()))

    # Compare the resources, and check which ones have changed
    for resource in new_res_set.list_resource_names():
        old_resource     = res_set.get_resource_by_name(resource)
        checked_resource = new_res_set.get_resource_by_name(resource)

        if old_resource.get_state() != checked_resource.get_state():
            attr = checked_resource.get_attribute_by_name(checked_resource.list_attribute_names()[0])
            print("ResCallBack: The status of resource '%s' has changed: %s -> %s" %
                  (resource, old_resource.get_state(),
                   checked_resource.get_state()))
            print("ResCallBack: Attribute %s = %s" % (attr.get_name(), attr.get_value()))

    # Remove and switch the userdata resource set to a new one
    res_set.update(new_res_set)

    opaque.res_set_changed = True

def create_res_set(conn, callback):
        conn.get_opaque_data().res_set = conn.create_resource_set(callback, "player")
        conn.get_opaque_data().res_set.create_resource("audio_playback")

        # Create two state dumps of our resource set for current/expected state
        conn.get_opaque_data().res_set_state = StateDump(conn.get_opaque_data().res_set)
        conn.get_opaque_data().res_set_expected_state = StateDump(conn.get_opaque_data().res_set)

def py_grab_resource_set(conn, callback):
    status = conn.get_opaque_data()

    # Create a resource set in case it doesn't exist
    if not conn.get_opaque_data().res_set:
        create_res_set(conn, callback)

    res_set = conn.get_opaque_data().res_set

    status.res_set_state.state = "acquired"
    for res in status.res_set_state.resources.itervalues():
        res.state = "acquired"

    if res_set.get_state() != "acquired":
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
        status.res_set_state.state = "acquired"
        for res in status.res_set_state.resources.itervalues():
            res.state = "acquired"
        return not res_set.acquire()
    else:
        return True

def py_check_result(conn):
    res_set = conn.get_opaque_data().res_set

    desired_state = conn.get_opaque_data().res_set_state

    curr_state = StateDump(res_set)

    if not desired_state.equals(curr_state):
        print("CheckResult: State did not meet expectations!")
        desired_state.print_differences(curr_state)
        return False
    else:
        print("CheckResult: State met expectations!")
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
            print("\t\tstate: %s != %s" % (self.state, other.state))

        for attr in self.attr_objects:
            attr.print_differences(other.attributes[attr.name])


class StateDump(object):
    def __init__(self, res_set):
        self.names     = []
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
            print("\tstate: %s != %s" % (self.state, other.state))

        for res in self.res_objects:
            res.print_differences(other.resources[res.name])
