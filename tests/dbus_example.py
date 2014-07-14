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

from mrp_dbus import (Connection, DBusConfig)
from mrp_dbus_helpers import (ChangeManager, example_callback, ResSetAddition,
                              ResourceAddition, AttributeModification, Acquisition,
                              ResourceRemoval, ResSetRemoval)

if __name__ == "__main__":
    # Create the object that is passed to the callback as user_data
    manager = ChangeManager()

    # Create a D-Bus configuration object and set the bus type to "session"
    config = DBusConfig()
    config.set_bus_type("session")

    # "Connect" to the D-Bus protocol
    conn = Connection(config)
    # Register a callback for additions and removals of resource sets
    conn.register_callback(example_callback, manager)

    # Try creating a resource set
    res_set = conn.create_resource_set()
    manager.add_change(conn, ResSetAddition(res_set.get_path()))
    conn.get_mainloop().run()

    # Register a callback for changes in the resource set
    res_set.register_callback(example_callback, manager)

    # Create a resource in the resource set with the type of the first available resource
    res = res_set.add_resource(res_set.list_available_resources()[0])
    manager.add_change(res_set, ResourceAddition(res.get_path()))
    conn.get_mainloop().run()

    # Register a callback for changes in the resource
    res.register_callback(example_callback, manager)
    # Get a list of attributes available in the resource
    attr_names = res.list_attribute_names()

    # Try setting the value of an attribute
    if not res.set_attribute_value(attr_names[0], -9001):
        print("Failed to request an attribute value change to the first attribute")
    manager.add_change(res, AttributeModification(attr_names[0], -9001))
    conn.get_mainloop().run()

    # And finally try requesting the resource set's resources
    if not res_set.request():
        print("Failed to request the resource set's contents")
    manager.add_change(res_set, Acquisition())
    manager.add_change(res, Acquisition())
    conn.get_mainloop().run()

    # Clean-up the resource and then the resource set
    manager.add_change(res_set, ResourceRemoval(res.get_path()))
    res_set.remove_resource(res)
    conn.get_mainloop().run()

    manager.add_change(conn, ResSetRemoval(res_set.get_path()))
    res_set.delete()
    conn.config.mainloop.run()
