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

from mrp_dbus import (Connection, DBusConfig, ResourceSet)
from random import sample
import dbus

config = DBusConfig()
config.set_bus_type("session")

conn = None
res_sets = []
resources = []
changes = dict()
conn_callback_set = False
res_set_callback_set = False
resource_callback_set = False


def test_callback(prop, value, original_thing, user_data):
    global changes
    print(">> PythonicCallback")

    # Basic per-callback debug log for property and new value
    print("PythonicCallback[%s]: %s = %s" % (type(original_thing), prop, value))

    if prop in changes:
        # We are adding things or modifying things
        if changes[prop][0] == "addition":
            if isinstance(value, dbus.Array):
                if changes[prop][1] in value:
                    del(changes[prop])
            elif isinstance(value, dbus.Dictionary):
                if changes[prop][1][0] in value and changes[prop][1][1] == value[changes[prop][1][0]]:
                    del(changes[prop])
            else:
                if changes[prop][1] == value:
                    del(changes[prop])
        elif changes[prop][0] == "acquisition":
            if isinstance(original_thing, ResourceSet) and changes[prop][1] == value:
                del(changes[prop])
        # We are removing things
        else:
            if isinstance(value, dbus.Array):
                if changes[prop][1] not in value:
                    del(changes[prop])
            else:
                if changes[prop][1] != value:
                    del(changes[prop])

    if not len(changes):
        user_data.reset_mainloop()

    print("<< PythonicCallback")


def value_to_be_set(type):
    return {
        dbus.String: "testString",
        dbus.Int32:  -9001,
        dbus.UInt32: 1192,
        dbus.Double: 3.14,
    }.get(type)


def connect():
    print(">>> Connect")
    global config, conn, conn_callback_set
    conn = Connection(config)
    print(conn.pretty_print())
    assert conn
    if not conn_callback_set:
        conn.register_callback(test_callback, config)
        conn_callback_set = True
    print("<<< Connect")


def disconnect():
    print(">>> Disconnect")
    global conn, res_sets
    for res_set in res_sets:
        assert res_set.delete()
        res_sets.remove(res_set)
    print(conn.pretty_print())
    print("<<< Disconnect")


def create_res_set():
    print(">>> CreateResSet")
    global conn, res_sets, changes, res_set_callback_set
    res_set = conn.create_resource_set()
    assert res_set
    if not res_set_callback_set:
        res_set.register_callback(test_callback, config)
        res_set_callback_set = True

    changes["resourceSets"] = ("addition", res_set.get_path())
    conn.get_mainloop().run()
    res_sets.append(res_set)
    print(conn.pretty_print())
    print("<<< CreateResSet")


def remove_res_set():
    print(">>> RemoveResSet")
    global conn, res_sets, res_set_callback_set
    res_set = res_sets.pop()
    changes["resourceSets"] = ("removal", res_set.get_path())
    assert res_set.delete()
    res_set_callback_set = False
    conn.get_mainloop().run()
    print(conn.pretty_print())
    print("<<< RemoveResSet")


def set_class():
    print(">>> SetClass")
    res_set = res_sets[0]
    res_set.set_class("navigator")
    changes["class"] = ("addition", "navigator")
    print(res_set.pretty_print())
    conn.get_mainloop().run()
    assert res_set.get_class() == "navigator"
    print("<<< SetClass")


def add_resource():
    print(">>> AddResource")
    global res_sets, resource_callback_set
    res_set = res_sets[0]
    res = res_set.add_resource(res_set.list_available_resources()[0])
    assert res
    if not resource_callback_set:
        res.register_callback(test_callback, config)
        resource_callback_set = True
    changes["resources"] = ("addition", res.get_path())
    conn.get_mainloop().run()
    print(res_set.pretty_print())
    print("<<< AddResource")


def remove_resource():
    print(">>> RemoveResource")
    global res_sets, resource_callback_set
    res_set = res_sets[0]
    res_name = res_set.list_resources()[0]
    res = res_set.get_resource(res_name)
    assert res
    changes["resources"] = ("removal", res.get_path())
    assert res_set.remove_resource(res)
    conn.get_mainloop().run()
    resource_callback_set = False
    assert res_name not in res_set.list_resources()
    print(res_set.pretty_print())
    print("<<< RemoveResource")


def modify_attribute():
    print(">>> ModifyAttribute")
    global res_sets
    res_set = res_sets[0]
    res = res_set.get_resource(sample(res_set.list_resources(), 1)[0])
    assert res

    attr_name = res.list_attribute_names()[0]
    assert attr_name

    attr_type = res.get_attribute_type(attr_name)
    print("ModifyAttribute: Setting attribute %s to value %s" % (attr_name, value_to_be_set(attr_type)))

    assert res.set_attribute_value(attr_name, value_to_be_set(attr_type))
    changes["attributes"] = ("addition", (attr_name, value_to_be_set(attr_type)))
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.get_attribute_value(attr_name) == value_to_be_set(attr_type)
    print("<<< ModifyAttribute")


def make_resource_mandatory():
    print(">>> MakeMandatory")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_mandatory()
    changes["mandatory"] = ("addition", True)
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.is_mandatory()
    print("<<< MakeMandatory")


def make_resource_nonessential():
    print(">>> MakeNonessential")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_mandatory(False)
    changes["mandatory"] = ("addition", False)
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert not res.is_mandatory()
    print("<<< MakeNonessential")
    pass


def make_resource_shareable():
    print(">>> MakeShareable")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_shareable()
    changes["shared"] = ("addition", True)
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.is_shareable()
    print("<<< MakeShareable")


def make_resource_unshareable():
    print(">>> MakeUnshareable")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_shareable(False)
    changes["shared"] = ("addition", False)
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert not res.is_shareable()
    print(">>> MakeUnshareable")
    pass


def acquire_set():
    print(">>> AcquireSet")
    global res_sets
    res_set = res_sets[0]
    assert res_set.request()
    changes["status"] = ("acquisition", "acquired")
    conn.get_mainloop().run()
    print(res_set.pretty_print())
    assert res_set.get_state() == "acquired"
    print("<<< AcquireSet")


def release_set():
    print(">>> ReleaseSet")
    global res_sets
    res_set = res_sets[0]
    assert res_set.release()
    changes["status"] = ("acquisition", "available")
    conn.get_mainloop().run()
    print(res_set.pretty_print())
    assert res_set.get_state() == "available"
    print("<<< ReleaseSet")
