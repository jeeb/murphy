#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mrp_resource_native import (Connection)
import sys


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


def actual_test_steps(conn):
    # Create a clean, empty new resource set
    print("Entered actual test steps")
    res_set = conn.create_resource_set(py_res_callback, "player")
    if not res_set:
        print("Failed to create a resource set")
        return False

    # We hold the currently worked upon res_set
    # in the opaque data
    conn.udata.opaque.res_set = res_set

    # Add the audio_playback resource to the empty set
    resource = res_set.create_resource("audio_playback")
    if not resource:
        print("Can has no resource")
        return False

    attr = resource.get_attribute_by_name(resource.list_attribute_names()[0])
    attr.set_value_to("huehue")

    acquired_status = res_set.acquire()

    return not acquired_status


def check_tests_results(conn):
    # Check new status
    res_set = conn.get_opaque_data().res_set
    if res_set.get_state() != "acquired":
        print("FirstTest: Something went wrong, resource set's not ours")
        return False
    else:
        print("FirstTest: Yay, checked that we now own the resource set")
        res  = res_set.get_resource_by_name("audio_playback")
        attr = res.get_attribute_by_name(res.list_attribute_names()[0])
        if attr.get_value() == "huehue":
            print("FirstTest: Yay, we have the first attribute set to 'huehue' now!")
            return True


class StatusObj():
    def __init__(self):
        self.res_set = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False
        self.res_set_changed         = False
        self.tests_successful        = False


if __name__ == "__main__":
    # Basic statuses
    test_run       = False
    check_run      = False
    test_succeeded = False

    # Create the general status object (passed on as opaque)
    status = StatusObj()

    # Create a connection object and try to connect to Murphy
    conn = Connection(py_status_callback, status)
    connected = conn.connect()
    if not connected:
        print("Main: Couldn't connect")
        sys.exit(2)

    # Run the actual changes
    finished_test = actual_test_steps(conn)
    if not finished_test:
        print("Main: Test not finished")
        conn.disconnect()
        sys.exit(3)

    # Check the results of the changes done
    while conn.iterate():
        print("res_set_changed: %s" % (status.res_set_changed))

        if not check_run and status.res_set_changed:
            test_succeeded = check_tests_results(conn)
            check_run = True
            break

    conn.disconnect()

    sys.exit(not (check_run and test_succeeded))
