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

from mrp_dbus import (Connection, DBusConfig, Resource, ResourceSet)
from mrp_dbus_helpers import StateDumpResource


class TestObject():
    def __init__(self):
        self.res_set_added     = False
        self.resource_added    = False
        self.value_modified    = False
        self.resource_acquired = False
        self.resource_removed  = False
        self.res_set_removed   = False

        self.res_set = None

    def all_true(self):
        return \
            self.res_set_added and \
            self.resource_added and \
            self.value_modified and \
            self.resource_removed and \
            self.resource_acquired and \
            self.res_set_removed


def pythonic_callback(prop, value, original_thing, user_data):
    print(">> PythonicCallback")

    # Basic per-callback debug log for property and new value
    print("PythonicCallback: %s = %s" % (prop, value))

    # Determine the type of object that sent the signal
    if isinstance(original_thing, Connection):
        if not user_data.res_set_added:
            if prop == "resourceSets" and user_data.res_set.get_path() in value:
                print("PythonicCallback: A Resource set has been added to connection!")
                user_data.res_set_added = True
        elif prop == "resourceSets" and user_data.res_set.get_path() not in value:
            print("PythonicCallback: Resource set has been cleaned up!")
            user_data.res_set_removed = True
    elif isinstance(original_thing, ResourceSet):
        if not user_data.resource_added:
            if prop == "resources" and len(value) > 0:
                print("PythonicCallback: Resource has been added to the set!")
                user_data.resource_added = True
        elif prop == "status" and value == "acquired":
            print("PythonicCallback: Resource set is acquired!")
        elif prop == "resources" and len(value) == 0:
            print("PythonicCallback: Resource has been removed from the set!")
            user_data.resource_removed = True
    elif isinstance(original_thing, Resource):
        if not user_data.value_modified:
            if prop == "attributes" and value.get("int") == -9001:
                print("PythonicCallback: Attribute in resource set is now set to requested value!")
                user_data.value_modified = True
        elif prop == "status" and value == "acquired":
            print("PythonicCallback: Resource is acquired!")
            user_data.resource_acquired = True

    # Check if all needed changes have happened, and quit mainloop in that case
    if user_data.all_true():
        print("PythonicCallback: All Done!")
        original_thing.get_mainloop().quit()

    print("<< PythonicCallback\n")


if __name__ == "__main__":
    # Create the object that is passed to the callback as user_data
    user_data = TestObject()

    # Create a D-Bus configuration object and set the bus type to "session"
    config = DBusConfig()
    config.set_bus_type("session")

    # "Connect" to the D-Bus protocol
    conn = Connection(config)
    # Register a callback for additions and removals of resource sets
    conn.register_callback(pythonic_callback, user_data)

    # Try creating a resource set
    res_set = conn.create_resource_set()

    # Save a reference to the resource set in user_data
    user_data.res_set = res_set

    # Register a callback for changes in the resource set
    res_set.register_callback(pythonic_callback, user_data)

    # Create a resource in the resource set with the type of the first available resource
    res = res_set.add_resource(res_set.list_available_resources()[0])
    # Try grabbing the first resource added to the resource set
    res_again = res_set.get_resource(res_set.list_resources()[0])

    if not res_again:
        print("Failed to get the same resource")

    # Test StateDumping
    dump = StateDumpResource(res)
    dump2 = StateDumpResource(res_again)
    dump.attributes["policy"] = "strict"

    if not dump.equals(dump2):
        dump.print_differences(dump2)
    else:
        exit(1)
    # End StateDumping test

    # Register a callback for changes in the resource
    res.register_callback(pythonic_callback, user_data)
    # Get a list of attributes available in the resource
    welp = res.list_attribute_names()

    # Try setting the value of an attribute
    if not res.set_attribute_value(welp[0], -9001):
        print("Failed to request an attribute value change to the first attribute")

    # And finally try requesting the resource set's resources
    if not res_set.request():
        print("Failed to request the resource set's contents")

    # Clean-up
    res_set.remove_resource(res)
    res_set.delete()

    # Run the mainloop to get the actual results in callback calls
    conn.config.mainloop.run()
