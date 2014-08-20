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

import os
os.environ["MRP_IN_TREE"] = "1"
from mrp_resource_native import (Connection)
from mrp_resource_native_helpers import (StatusObj,
                                         py_status_callback,
                                         get_test_value_by_type,
                                         check_results,
                                         update_state_dumps,
                                         new_res_callback)

status = StatusObj()
conn = Connection(py_status_callback, status)
res_set = None
classes = None
res_names = None
resource = None
attr_names = None


def connect():
    global conn
    assert conn.connect()


def disconnect():
    global conn
    conn.get_opaque_data().res_set_changed = False

    if conn.get_opaque_data().res_set:
        conn.get_opaque_data().res_set = None

    update_state_dumps(conn, None)

    conn.disconnect()
    print("We disconnect")
    print("")


def create_res_set():
    global conn, res_set, classes
    res_set = conn.create_resource_set(new_res_callback, classes[0])
    assert res_set

    conn.get_opaque_data().res_set = res_set
    update_state_dumps(conn, res_set)


def get_class_list():
    global conn, classes
    classes = conn.list_application_classes()
    assert classes


def list_system_resources():
    global conn, res_names
    temp_set = conn.list_resources()
    res_names = temp_set.list_resource_names()
    assert res_names


def remove_res_set():
    global res_set
    res_set.delete()
    res_set = None
    update_state_dumps(conn, None)


def switch_autorelease(value_to_set):
    global res_set
    assert res_set.set_autorelease(value_to_set)


def add_resource():
    global res_set, res_names, resource
    resource = res_set.create_resource(res_names[0])
    update_state_dumps(conn, res_set)
    assert resource


def remove_resource():
    global res_set, resource
    res_set.delete_resource(resource)
    update_state_dumps(conn, res_set)
    resource = None


def update_resource():
    global resource
    resource = None
    resource = res_set.get_resource_by_name(res_names[0])


def acquire_set():
    global res_set
    result, error = res_set.acquire()
    if not result:
        print("Acquisition failed due to error: %s" % (error))

    assert result

    conn.get_opaque_data().res_set_state.set_acquired()
    check_results(conn)

    # And, for now at least, we will have to update the resource, as it is now invalid
    update_resource()


def release_set():
    global res_set
    result, error = res_set.release()
    if not result:
        print("Release failed due to error: %s" % (error))

    assert result

    conn.get_opaque_data().res_set_state.set_released()
    check_results(conn)

    # And, for now at least, we will have to update the resource, as it is now invalid
    update_resource()


def list_attribute_names():
    global resource, attr_names
    attr_names = resource.list_attribute_names()
    assert attr_names


def modify_attribute():
    global resource, attr_names
    attribute = resource.get_attribute_by_name(attr_names[0])
    assert attribute
    assert attribute.set_value_to(get_test_value_by_type(attribute.get_type()))
    update_state_dumps(conn, res_set)
