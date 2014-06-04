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

def py_grab_resource_set(conn, callback):
    print("Entered actual test steps")

    # Create a resource set in case it doesn't exist
    if not conn.get_opaque_data().res_set:
        create_res_set(conn, callback)

    res_set = conn.get_opaque_data().res_set

    if res_set.get_state() != "acquired":
        return not res_set.acquire()
    else:
        return True

def py_modify_attribute(conn, callback, name, value):
    # Create a resource set in case it doesn't exist
    if not conn.get_opaque_data().res_set:
        create_res_set(conn, callback)

    # Otherwise just use the resource set in the opaque data
    res_set = conn.get_opaque_data().res_set
    # If the resource set is already there, we probably have the res_set too
    res = res_set.get_resource_by_name("audio_playback")
    result = res.get_attribute_by_name(name).set_value_to(value)

    if res_set.get_state() != "acquired":
        return not res_set.acquire()
    else:
        return True

def py_check_result(conn):
    res_set = conn.get_opaque_data().res_set
    if res_set.get_state() != "acquired":
        print("FirstTest: Something went wrong, resource set's not ours")
        return False
    else:
        print("FirstTest: Yay, checked that we now own the resource set")
        return True

class StatusObj():
    def __init__(self):
        self.res_set = None

        self.conn_status_callback_called = False
        self.connected_to_murphy     = False
        self.res_set_changed         = False
        self.tests_successful        = False
