import os
os.environ["MRP_IN_TREE"] = "1"
from mrp_resource_native import (Connection)
from mrp_resource_native_helpers import (StatusObj,
                                         py_status_callback,
                                         py_res_callback,
                                         py_grab_resource_set,
                                         py_check_result,
                                         py_modify_attribute,
                                         StateDump)


attr_name = "role"
attr_val = "testing_testing"

status = StatusObj()
conn = Connection(py_status_callback, status)
res_sets = []

def value_to_be_set(type):
    return {
        "s": "testString",
        "i": -9001,
        "u": 1192,
        "f": 3.14,
    }.get(type)

def local_callback(new_res_set, opaque):
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

def connect():
    global conn
    assert conn.connect()


def disconnect():
    global conn
    conn.get_opaque_data().res_set_changed = False

    if conn.get_opaque_data().res_set:
        conn.get_opaque_data().res_set.delete()
        conn.get_opaque_data().res_set = None

    conn.disconnect()
    print("We disconnect")
    print("")


def create_res_set():
    global res_sets
    pre_count = len(res_sets)
    res_set = conn.create_resource_set(py_res_callback, conn.list_application_classes()[0])
    res_sets.append(res_set)
    after_count = len(res_sets)
    assert (after_count - pre_count) == 1


def remove_res_set():
    global res_sets
    pre_count = len(res_sets)
    assert pre_count
    set = res_sets[0]
    print(len(set.list_resource_names()))
    set.delete()
    res_sets.remove(set)
    after_count = len(res_sets)
    assert (pre_count - after_count) == 1


def set_class():
    pass # These parts of resources cannot be modified after the fact in this API


def add_resource():
    global conn
    res_list = conn.list_resources()
    res_names = res_list.list_resource_names()

    assert res_sets[0].create_resource(res_names[0])


def remove_resource():
    global res_sets
    assert len(res_sets)
    set = res_sets[0]
    name_list = set.list_resource_names()
    assert len(name_list)
    name = name_list[0]
    set.delete_resource_by_name(name)
    print("beep")


def modify_attribute():
    global res_sets
    res = res_sets[0].get_resource_by_name(res_sets[0].list_resource_names()[0])
    attr = res.get_attribute_by_name(res.list_attribute_names()[0])
    assert attr.set_value_to(value_to_be_set(attr.get_type()))


def make_resource_mandatory():
    pass # These parts of resources cannot be modified after the fact in this API


def make_resource_nonessential():
    pass # These parts of resources cannot be modified after the fact in this API


def make_resource_shareable():
    pass # These parts of resources cannot be modified after the fact in this API


def make_resource_unshareable():
    pass # These parts of resources cannot be modified after the fact in this API


def acquire_set():
    global res_sets
    assert len(res_sets)
    set = res_sets[0]
    assert set.acquire()[0]


def release_set():
    global res_sets
    assert len(res_sets)
    set = res_sets[0]
    assert set.release()[0]


def issue_resource_order():
    global conn
    assert py_grab_resource_set(conn, py_res_callback)


def issue_attribute_order():
    global conn
    assert py_modify_attribute(conn, py_res_callback, attr_name, attr_val)


def check_for_order_completion():
    global conn
    if conn.get_opaque_data().res_set.get_state() == "acquired":
        return

    while conn.iterate():
        print("Iterated: res_set_changed = %s" % (conn.get_opaque_data().res_set_changed))
        if conn.get_opaque_data().res_set_changed:
            py_check_result(conn)
            return


def connected():
    global conn
    assert conn.get_state() == "connected"
