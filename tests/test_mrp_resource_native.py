import os
os.environ["MRP_IN_TREE"] = "1"
from mrp_resource_native import (Connection)
from mrp_resource_native_helpers import (StatusObj,
                                         py_status_callback,
                                         py_res_callback,
                                         py_grab_resource_set,
                                         py_check_result,
                                         py_modify_attribute)


attr_name = "role"
attr_val = "testing_testing"

status = StatusObj()
conn = Connection(py_status_callback, status)
res_set = None


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
