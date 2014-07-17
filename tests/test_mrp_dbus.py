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
from mrp_dbus_helpers import (ChangeManager, ResSetAddition, ResSetRemoval,
                              ClassModification, ResourceAddition, ResourceRemoval,
                              AttributeModification, MandatorynessModification,
                              SharingModification, Acquisition, Release, example_callback)
from random import sample
import dbus

config = DBusConfig()
config.set_bus_type("session")

conn = None
res_sets = []
resources = []

c_manager = ChangeManager()


def value_to_be_set(type):
    return {
        dbus.String: "testString",
        dbus.Int32:  -9001,
        dbus.UInt32: 1192,
        dbus.Double: 3.14,
    }.get(type)


def connect():
    print(">>> Connect")
    global config, conn

    conn = Connection(config)
    print(conn.pretty_print())
    assert conn

    conn.register_callback(example_callback, c_manager)
    print("<<< Connect")


def disconnect():
    print(">>> Disconnect")
    global conn, res_sets
    for res_set in res_sets:
        assert res_set.delete()
        res_sets.remove(res_set)

    print(conn.pretty_print())
    conn.get_mainloop().quit()
    conn = None

    print("<<< Disconnect")


def create_res_set():
    print(">>> CreateResSet")
    global conn, res_sets

    res_set = conn.create_resource_set()
    assert res_set

    res_set.register_callback(example_callback, c_manager)
    c_manager.add_change(conn, ResSetAddition(res_set.get_path()))

    conn.get_mainloop().run()
    res_sets.append(res_set)

    print(conn.pretty_print())
    print("<<< CreateResSet")


def remove_res_set():
    print(">>> RemoveResSet")
    global conn, res_sets

    res_set = res_sets.pop()

    c_manager.remove_changes(res_set)
    c_manager.add_change(conn, ResSetRemoval(res_set.get_path()))
    assert res_set.delete()

    conn.get_mainloop().run()

    print(conn.pretty_print())
    print("<<< RemoveResSet")


def set_class(failure_expected=False):
    print(">>> SetClass")

    res_set = res_sets[0]

    if failure_expected:
        assert not res_set.set_class("navigator")
    else:
        assert res_set.set_class("navigator")
        c_manager.add_change(res_set, ClassModification("navigator"))
        conn.get_mainloop().run()
        assert res_set.get_class() == "navigator"

    print(res_set.pretty_print())
    print("<<< SetClass")


def add_resource():
    print(">>> AddResource")
    global res_sets

    res_set = res_sets[0]
    res = res_set.add_resource(res_set.list_available_resources()[0])
    assert res
    res.register_callback(example_callback, c_manager)
    c_manager.add_change(res_set, ResourceAddition(res.get_path()))

    conn.get_mainloop().run()

    print(res_set.pretty_print())
    print("<<< AddResource")


def remove_resource():
    print(">>> RemoveResource")
    global res_sets

    res_set = res_sets[0]
    res_name = res_set.list_resources()[0]
    res = res_set.get_resource(res_name)
    assert res

    c_manager.remove_changes(res)
    c_manager.add_change(res_set, ResourceRemoval(res.get_path()))
    assert res_set.remove_resource(res)

    conn.get_mainloop().run()
    assert res_name not in res_set.list_resources()

    print(res_set.pretty_print())
    print("<<< RemoveResource")


def modify_attribute(failure_expected=False):
    print(">>> ModifyAttribute")
    global res_sets

    res_set = res_sets[0]
    res = res_set.get_resource(sample(res_set.list_resources(), 1)[0])
    assert res

    attr_name = res.list_attribute_names()[0]
    assert attr_name
    attr_type = res.get_attribute_type(attr_name)

    print("ModifyAttribute: Setting attribute %s to value %s" % (attr_name, value_to_be_set(attr_type)))

    if failure_expected:
        assert not res.set_attribute_value(attr_name, value_to_be_set(attr_type))
    else:
        assert res.set_attribute_value(attr_name, value_to_be_set(attr_type))
        c_manager.add_change(res, AttributeModification(attr_name, value_to_be_set(attr_type)))
        conn.get_mainloop().run()
        assert res.get_attribute_value(attr_name) == value_to_be_set(attr_type)

    print(res.pretty_print())
    print("<<< ModifyAttribute")


def make_resource_mandatory(failure_expected=False):
    print(">>> MakeMandatory")

    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])

    if failure_expected:
        assert not res.make_mandatory()
    else:
        assert res.make_mandatory()
        c_manager.add_change(res, MandatorynessModification(True))
        conn.get_mainloop().run()
        assert res.is_mandatory()

    print(res.pretty_print())
    print("<<< MakeMandatory")


def make_resource_nonessential(failure_expected=False):
    print(">>> MakeNonessential")

    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])

    if failure_expected:
        assert not res.make_mandatory(False)
    else:
        assert res.make_mandatory(False)
        c_manager.add_change(res, MandatorynessModification(False))
        conn.get_mainloop().run()
        assert not res.is_mandatory()

    print(res.pretty_print())
    print("<<< MakeNonessential")
    pass


def make_resource_shareable(failure_expected=False):
    print(">>> MakeShareable")

    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])

    if failure_expected:
        assert not res.make_shareable()
    else:
        assert res.make_shareable()
        c_manager.add_change(res, SharingModification(True))
        conn.get_mainloop().run()
        assert res.is_shareable()

    print(res.pretty_print())
    print("<<< MakeShareable")


def make_resource_unshareable(failure_expected=False):
    print(">>> MakeUnshareable")

    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])

    if failure_expected:
        assert not res.make_shareable(False)
    else:
        assert res.make_shareable(False)
        c_manager.add_change(res, SharingModification(False))
        conn.get_mainloop().run()
        assert not res.is_shareable()

    print(res.pretty_print())
    print(">>> MakeUnshareable")
    pass


def acquire_set():
    print(">>> AcquireSet")
    global res_sets

    res_set = res_sets[0]

    assert res_set.request()
    c_manager.add_change(res_set, Acquisition())
    conn.get_mainloop().run()
    assert res_set.get_state() == "acquired"

    print(res_set.pretty_print())
    print("<<< AcquireSet")


def release_set():
    print(">>> ReleaseSet")
    global res_sets

    res_set = res_sets[0]
    will_we_get_callback = not (res_set.get_state() != "acquired")

    assert res_set.release()
    if will_we_get_callback:
        c_manager.add_change(res_set, Release())
        conn.get_mainloop().run()
        assert res_set.get_state() == "available"

    print(res_set.pretty_print())
    print("<<< ReleaseSet")
