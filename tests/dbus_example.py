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

from mrp_dbus import (Connection, DBusConfig, Resource)


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

    # Basic per-callback log
    print("PythonicCallback: %s = %s" % (prop, value))

    if prop == "resourceSets" and value.count(user_data.res_set) > 0:
        print("PythonicCallback: Resource set is now added")
        user_data.res_set_added = True
    elif prop == "resources" and len(value) > 0:
        print("PythonicCallback: There is now resources!")
        user_data.resource_added = True
    elif prop == "attributes" and value.get("int") == -9001:
        print("PythonicCallback: The attribute is now set!")
        user_data.value_modified = True
    elif prop == "status" and value == "acquired":
        if isinstance(original_thing, Resource):
            print("PythonicCallback: The resource is acquired!")
            user_data.resource_acquired = True
        else:
            print("PythonicCallback: The resource set is acquired!")
    elif prop == "resources" and len(value) == 0:
        print("PythonicCallback: The resource has been removed from the set!")
        user_data.resource_removed = True
    elif prop == "resourceSets" and value.count(user_data.res_set) == 0:
        print("PythonicCallback: The resource set has been cleaned up!")
        user_data.res_set_removed = True

    if user_data.all_true():
        print("PythonicCallback: All Done!")
        original_thing.get_mainloop().quit()

    print("<< PythonicCallback\n")


if __name__ == "__main__":
    user_data = TestObject()
    conn = Connection(DBusConfig())
    conn.register_callback(pythonic_callback, user_data)
    res_set = conn.create_resource_set()
    user_data.res_set = res_set.set_path
    res_set.register_callback(pythonic_callback, user_data)

    res = res_set.add_resource(res_set.list_available_resources()[0])
    res.register_callback(pythonic_callback, user_data)
    welp = res.list_attributes()
    if not res.set_attribute_value(welp[0], -9001):
        print("Perkele3")

    if not res_set.request():
        print("Perkele2")

    res_set.remove_resource(res)
    res_set.delete()

    conn.config.mainloop.run()
