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
from random import sample
import dbus

config = DBusConfig()
config.set_bus_type("session")

conn = None
res_sets = []
resources = []
conn_callback_set = False
res_set_callback_set = False
resource_callback_set = False


# Things we can actually add, such as resources or sets
class Addition(object):
    def __init__(self, name, added_path):
        self.name = name
        self.added_path = added_path

    def get_name(self):
        return self.name

    def check(self, path, list_of_values):
        return path == self.name and self.added_path in list_of_values


class ResSetAddition(Addition):
    def __init__(self, path):
        super(ResSetAddition, self).__init__("resourceSets", path)


class ResourceAddition(Addition):
    def __init__(self, path):
        super(ResourceAddition, self).__init__("resources", path)
        pass


# Same as the previous, just reverse
class Removal(object):
    def __init__(self, name, removed_path):
        self.name = name
        self.removed_path = removed_path

    def get_name(self):
        return self.name

    def check(self, path, list_of_values):
        return path == self.name and self.removed_path not in list_of_values


class ResSetRemoval(Removal):
    def __init__(self, path):
        super(ResSetRemoval, self).__init__("resourceSets", path)


class ResourceRemoval(Removal):
    def __init__(self, path):
        super(ResourceRemoval, self).__init__("resources", path)


# Modification of values, attributes
class Modification(object):
    def __init__(self, name, modification):
        self.name = name
        self.modification = modification

    def get_name(self):
        return self.name

    def check(self, key, value):
        return self.name == key and self.modification == value


class ClassModification(Modification):
    def __init__(self, new_class):
        super(ClassModification, self).__init__("class", new_class)


class AttributeModification(Modification):
    def __init__(self, attr_name, new_attr_value):
        super(AttributeModification, self).__init__("attributes", (attr_name, new_attr_value))

    def check(self, key, value):
        name = self.modification[0]
        val = self.modification[1]
        return key == "attributes" and name in value and value[name] == val


class MandatorynessModification(Modification):
    def __init__(self, bool):
        super(MandatorynessModification, self).__init__("mandatory", bool)


class SharingModification(Modification):
    def __init__(self, bool):
        super(SharingModification, self).__init__("shared", bool)


class Acquisition(Modification):
    def __init__(self):
        super(Acquisition, self).__init__("status", "acquired")


class Release(Modification):
    def __init__(self):
        super(Release, self).__init__("status", "available")


# Basic design is (modified_object, list_of_changes)
class ChangeManager():
    def __init__(self):
        self.change_sets = dict()

    def get_changes(self, object):
        path = object.get_path()
        if path in self.change_sets:
            return self.change_sets[path]
        else:
            return None

    def add_change(self, object, change):
        path = object.get_path()
        if path in self.change_sets:
            self.change_sets[path].append(change)
        else:
            self.change_sets[path] = [change]

    def remove_change(self, object, change):
        path = object.get_path()
        if path in self.change_sets:
            self.change_sets[path].remove(change)
            if not len(self.change_sets[path]):
                del(self.change_sets[path])
            return True
        else:
            return False

    def remove_changes(self, object):
        path = object.get_path()
        if path in self.change_sets:
            del(self.change_sets[path])

    def changes_available(self):
        return bool(len(self.change_sets))

    def was_this_an_expected_change(self, object, key, value):
        available_changes = self.get_changes(object)
        print("Beep: %s" % (available_changes))
        if available_changes:
            for c in available_changes:
                if c.check(key, value):
                    print(c)
                    self.remove_change(object, c)
                    return True

        return False

c_manager = ChangeManager()


def test_callback(prop, value, original_thing, user_data):
    print(">> PythonicCallback")

    # Basic per-callback debug log for property and new value
    print("PythonicCallback[%s]: %s = %s" % (str(original_thing), prop, value))

    # Using the ChangeManager to handle incoming changes
    if c_manager.was_this_an_expected_change(original_thing, prop, value):
        print("PythonicCallback: This change was expected!")
    else:
        print("PythonicCallback: This change was not expected")

    # When we are no longer expecting new changes, we stop the mainloop
    if not c_manager.changes_available():
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
    global conn, res_sets, res_set_callback_set
    res_set = conn.create_resource_set()
    assert res_set
    if not res_set_callback_set:
        res_set.register_callback(test_callback, config)
        res_set_callback_set = True

    c_manager.add_change(conn, ResSetAddition(res_set.get_path()))
    conn.get_mainloop().run()
    res_sets.append(res_set)
    print(conn.pretty_print())
    print("<<< CreateResSet")


def remove_res_set():
    print(">>> RemoveResSet")
    global conn, res_sets, res_set_callback_set
    res_set = res_sets.pop()
    c_manager.remove_changes(res_set)
    c_manager.add_change(conn, ResSetRemoval(res_set.get_path()))
    assert res_set.delete()
    res_set_callback_set = False
    conn.get_mainloop().run()
    print(conn.pretty_print())
    print("<<< RemoveResSet")


def set_class():
    print(">>> SetClass")
    res_set = res_sets[0]
    res_set.set_class("navigator")
    c_manager.add_change(res_set, ClassModification("navigator"))
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
    c_manager.add_change(res_set, ResourceAddition(res.get_path()))
    r_list = res_set.list_resources()
    print(r_list)
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
    c_manager.remove_changes(res)
    c_manager.add_change(res_set, ResourceRemoval(res.get_path()))
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
    c_manager.add_change(res, AttributeModification(attr_name, value_to_be_set(attr_type)))
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.get_attribute_value(attr_name) == value_to_be_set(attr_type)
    print("<<< ModifyAttribute")


def make_resource_mandatory():
    print(">>> MakeMandatory")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_mandatory()
    c_manager.add_change(res, MandatorynessModification(True))
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.is_mandatory()
    print("<<< MakeMandatory")


def make_resource_nonessential():
    print(">>> MakeNonessential")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_mandatory(False)
    c_manager.add_change(res, MandatorynessModification(False))
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
    c_manager.add_change(res, SharingModification(True))
    conn.get_mainloop().run()
    print(res.pretty_print())
    assert res.is_shareable()
    print("<<< MakeShareable")


def make_resource_unshareable():
    print(">>> MakeUnshareable")
    res_set = res_sets[0]
    res = res_set.get_resource(res_set.list_resources()[0])
    res.make_shareable(False)
    c_manager.add_change(res, SharingModification(False))
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
    c_manager.add_change(res_set, Acquisition())
    conn.get_mainloop().run()
    print(res_set.pretty_print())
    assert res_set.get_state() == "acquired"
    print("<<< AcquireSet")


def release_set():
    print(">>> ReleaseSet")
    global res_sets
    res_set = res_sets[0]
    assert res_set.release()
    c_manager.add_change(res_set, Release())
    conn.get_mainloop().run()
    print(res_set.pretty_print())
    assert res_set.get_state() == "available"
    print("<<< ReleaseSet")
