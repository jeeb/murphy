import os
os.environ["MRP_IN_TREE"] = "1"
from mrp_resource_native import (Connection)
from mrp_resource_native_helpers import (StatusObj,
                                         py_status_callback,
                                         get_test_value_by_type,
                                         new_res_callback,
                                         update_state_dumps,
                                         check_results)


attr_name = "role"
attr_val = "testing_testing"

status = StatusObj()
conn = Connection(py_status_callback, status)
res_sets = []


def connect():
    global conn
    assert conn.connect()


def disconnect():
    global conn, res_sets

    # Remove all leftover resource sets
    for set in res_sets:
        set.delete()

    # Reset the list
    res_sets = []

    # Reset information stored in the opaque user data
    if conn.get_opaque_data().res_set:
        conn.get_opaque_data().res_set = None

    conn.disconnect()
    print("We disconnect")
    print("")


def create_res_set():
    global conn, res_sets

    pre_count = len(res_sets)

    res_set = conn.create_resource_set(new_res_callback, conn.list_application_classes()[0])
    assert res_set
    res_sets.append(res_set)

    # Set the information stored in the opaque user data
    conn.get_opaque_data().res_set = res_set
    update_state_dumps(conn, res_set)

    after_count = len(res_sets)
    assert (after_count - pre_count) == 1


def remove_res_set():
    global conn, res_sets

    # Count things and make sure that we have at least one resource set in the list
    pre_count = len(res_sets)
    assert pre_count

    # Remove the actual resource set
    set = res_sets[0]
    set.delete()
    res_sets.remove(set)

    # Reset information stored in the opaque user data
    update_state_dumps(conn, None)

    conn.get_opaque_data().res_set_changed = False
    conn.get_opaque_data().res_set = None

    # Make sure that the new count of resource sets is according to expectations
    after_count = len(res_sets)
    assert (pre_count - after_count) == 1


def set_class(failure_expected=False):
    pass  # These parts of resources cannot be modified after the fact in this API


def add_resource():
    global conn, res_sets

    set = res_sets[0]
    res_list = conn.list_resources()
    res_names = res_list.list_resource_names()

    assert set.create_resource(res_names[0])
    # Update the state dumps in opaque user data
    update_state_dumps(conn, set)


def remove_resource():
    global conn, res_sets

    set = res_sets[0]
    res_names = set.list_resource_names()
    assert len(res_names)

    name = res_names[0]

    set.delete_resource_by_name(name)
    # Update the state dumps in opaque user data
    update_state_dumps(conn, set)


def modify_attribute(failure_expected=False):
    global res_sets

    res = res_sets[0].get_resource_by_name(res_sets[0].list_resource_names()[0])
    attr = res.get_attribute_by_name(res.list_attribute_names()[0])
    assert attr.set_value_to(get_test_value_by_type(attr.get_type()))

    if not failure_expected:
        update_state_dumps(conn, res_sets[0])


def make_resource_mandatory():
    pass  # These parts of resources cannot be modified after the fact in this API


def make_resource_nonessential():
    pass  # These parts of resources cannot be modified after the fact in this API


def make_resource_shareable():
    pass  # These parts of resources cannot be modified after the fact in this API


def make_resource_unshareable():
    pass  # These parts of resources cannot be modified after the fact in this API


def acquire_set():
    global res_sets
    assert len(res_sets)
    set = res_sets[0]
    assert set.acquire()[0]
    conn.get_opaque_data().res_set_state.set_acquired()
    check_results(conn)


def release_set():
    global res_sets
    assert len(res_sets)
    set = res_sets[0]
    assert set.release()[0]
    conn.get_opaque_data().res_set_state.set_released()
    check_results(conn)
