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
from mrp_resource_native_helpers import (py_res_callback, py_status_callback, StatusObj)
import sys


def actual_test_steps(conn):
    # Create a clean, empty new resource set
    print("Entered actual test steps")
    res_set = conn.create_resource_set(py_res_callback, "player")
    if not res_set:
        print("Failed to create a resource set")
        return False

    # We hold the currently worked upon res_set
    # in the opaque data
    conn.get_opaque_data().res_set = res_set

    # Add the audio_playback resource to the empty set
    resource = res_set.create_resource("audio_playback")
    if not resource:
        print("Can has no resource")
        return False

    attr = resource.get_attribute_by_name(resource.list_attribute_names()[0])
    if attr:
        print("Setting attribute val retcode: %s" % attr.set_value_to("huehue") )

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

    status.res_set.delete()

    conn.disconnect()

    sys.exit(not (check_run and test_succeeded))
