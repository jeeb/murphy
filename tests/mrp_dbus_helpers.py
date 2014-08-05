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

import dbus


# Ismo's pretty printing functions
def pretty_str_dbus_value(val, level=0, suppress=False):
    """
    Returns a string that contains a human-readable representation of the
    contents of a D-Bus value returned by Murphy's D-Bus API

    :param val:      D-Bus value to represent
    :param level:    Integer representing the indentation level of this element
    :param suppress: Boolean, skip indentation for non-array/dictionary types
    :return:         String containing the representation
    """
    if type(val) == dbus.Array:
        return pretty_str_dbus_array(val, level)
    elif type(val) == dbus.Dictionary:
        return pretty_str_dbus_dict(val, level)
    else:
        s = ""
        if not suppress:
            s += level * "\t"
        if type(val) == dbus.Boolean:
            if val:
                s += "True"
            else:
                s += "False"
        else:
            s += str(val)
        return s


def pretty_str_dbus_array(arr, level=0):
    """
    Returns a string that contains a human-readable representation of the
    contents of a D-Bus array

    :param arr:   D-Bus array to represent
    :param level: Integer representing the indentation level of this element
    :return:      String containing the representation
    """
    prefix = level * "\t"
    s = "[\n"
    for v in arr:
        s += pretty_str_dbus_value(v, level+1)
        s += "\n"
    s += prefix + "]"
    return s


def pretty_str_dbus_dict(d, level=0):
    """
    Returns a string that contains a human-readable representation of the
    contents of a D-Bus dictionary

    :param d:     D-Bus dictionary to represent
    :param level: Integer representing the indentation level of this element
    :return:      String containing the representation
    """
    prefix = level * "\t"
    s = "{\n"
    for k, v in d.items():
        s += prefix + "\t"
        s += str(k) + ": "
        s += pretty_str_dbus_value(v, level+1, True)
        s += "\n"
    s += prefix + "}"
    return s


def get_test_value_by_type(type):
    """
    Returns a value meant for testing of a given D-Bus value type

    :param type: D-Bus type for which an example value is needed.
                 Currently implemented types are as follows:
                 * dbus.String
                 * dbus.Int32
                 * dbus.UInt32
                 * dbus.Double

    :return:     An example value for a given D-Bus type
    """
    return {
        dbus.String: "testString",
        dbus.Int32:  -9001,
        dbus.UInt32: 1192,
        dbus.Double: 3.14,
    }.get(type)


def example_callback(prop, value, original_thing, user_data):
    """
    Example callback implementation that expects a ChangeManager object
    as user_data.

    :param prop:           Name of the property for which a signal was received
    :param value:          Updated value of that property
    :param original_thing: Object from which this signal callback was registered from
    :param user_data:      Undefined "user data" object, which one sets when
                           registering the callback. This example implementation
                           requires it to be an instance of ChangeManager

    :return: Void
    """
    print(">> PythonicCallback")

    # Basic per-callback debug log for property and new value
    print("PythonicCallback[%s]: %s = %s" % (str(original_thing), prop, value))

    # Using the ChangeManager to handle incoming changes
    if user_data.was_this_an_expected_change(original_thing, prop, value):
        print("PythonicCallback: This change was expected!")
    else:
        print("PythonicCallback: This change was not expected")

    # When we are no longer expecting new changes, we stop the mainloop
    if not user_data.changes_available():
        original_thing.reset_mainloop()

    print("<< PythonicCallback")


# Things we can actually add, such as resources or sets
class Addition(object):
    """
    Base class for changes that add something into a list of things
    """
    def __init__(self, name, added_path):
        self.name = name
        self.added_path = added_path

    def get_name(self):
        return self.name

    def check(self, path, list_of_values):
        return path == self.name and self.added_path in list_of_values


class ResSetAddition(Addition):
    """
    Subclass that wraps adding resource sets to a connection
    """
    def __init__(self, path):
        super(ResSetAddition, self).__init__("resourceSets", path)


class ResourceAddition(Addition):
    """
    Subclass that wraps adding resources to sets
    """
    def __init__(self, path):
        super(ResourceAddition, self).__init__("resources", path)
        pass


# Same as the previous, just reverse
class Removal(object):
    """
    Base class for changes that remove something from a list of things
    """
    def __init__(self, name, removed_path):
        self.name = name
        self.removed_path = removed_path

    def get_name(self):
        return self.name

    def check(self, path, list_of_values):
        return path == self.name and self.removed_path not in list_of_values


class ResSetRemoval(Removal):
    """
    Subclass that wraps removing resource sets from a connection
    """
    def __init__(self, path):
        super(ResSetRemoval, self).__init__("resourceSets", path)


class ResourceRemoval(Removal):
    """
    Subclass that wraps removing resources from sets
    """
    def __init__(self, path):
        super(ResourceRemoval, self).__init__("resources", path)


# Modification of values, attributes
class Modification(object):
    """
    Base class for changes that modify a value
    """
    def __init__(self, name, modification):
        self.name = name
        self.modification = modification

    def get_name(self):
        return self.name

    def check(self, key, value):
        return self.name == key and self.modification == value


class ClassModification(Modification):
    """
    Subclass that wraps modification of a resource set's class
    """
    def __init__(self, new_class):
        super(ClassModification, self).__init__("class", new_class)


class AttributeModification(Modification):
    """
    Subclass that wraps modification of a resource's attribute
    """
    def __init__(self, attr_name, new_attr_value):
        super(AttributeModification, self).__init__("attributes", (attr_name, new_attr_value))

    def check(self, key, value):
        name = self.modification[0]
        val = self.modification[1]
        return key == "attributes" and name in value and value[name] == val


class MandatorynessModification(Modification):
    """
    Subclass that wraps modification of a resource's mandatory field
    """
    def __init__(self, bool):
        super(MandatorynessModification, self).__init__("mandatory", bool)


class SharingModification(Modification):
    """
    Subclass that wraps modification of a resource's shared field
    """
    def __init__(self, bool):
        super(SharingModification, self).__init__("shared", bool)


class Acquisition(Modification):
    """
    Subclass that wraps modification of a resource's available field
    """
    def __init__(self):
        super(Acquisition, self).__init__("status", "acquired")


class Release(Modification):
    """
    Subclass that wraps modification of a resource's available field
    """
    def __init__(self):
        super(Release, self).__init__("status", "available")


# Basic design is (modified_object, list_of_changes)
class ChangeManager():
    def __init__(self):
        """
        A wrapper that connects changes (Additions, Removals and Modifications) to specific
        objects. Uses a dict based on the D-Bus paths of objects (in case of Murphy
        these should be unique per daemon run (The numeration will reset if Murphy
        is restarted).

        :return: Void
        """
        self.change_sets = dict()

    def get_changes(self, object):
        """
        Gets the changes specific to an object

        :param object: Object the changes of which are to be returned
        :return:       None if there are no changes recorded for this object,
                       otherwise a list of changes recorded for this object
        """
        path = object.get_path()
        if path in self.change_sets:
            return self.change_sets[path]
        else:
            return None

    def add_change(self, object, change):
        """
        Adds a change to the list of changes recorded for a given object. In
        case the object has not yet been recorded, a single-item list will be
        created of the given change

        :param object: Object for which the change will be recorded
        :param change: Change that will be recorded
        :return:       Void
        """
        path = object.get_path()
        if path in self.change_sets:
            self.change_sets[path].append(change)
        else:
            self.change_sets[path] = [change]

    def remove_change(self, object, change):
        """
        Removes a change from the list of recorded changes for a given object.
        In case the list becomes empty by means of this removal, the object
        gets removed from the dictionary.

        :param object: Object for which the change has been recorded
        :param change: Change that will be removed from record
        :return:       False if unsuccessful, True if successful
        """
        path = object.get_path()
        if path in self.change_sets:
            self.change_sets[path].remove(change)
            if not len(self.change_sets[path]):
                del(self.change_sets[path])
            return True
        else:
            return False

    def remove_changes(self, object):
        """
        Removes all changes from the list of recorded changes for a given object,
        and the object itself is purged from the dictionary

        :param object: Object which is to be cleansed
        :return:       False if unsuccessful, True if successful
        """
        path = object.get_path()
        if path in self.change_sets:
            del(self.change_sets[path])
            return True
        else:
            return False

    def changes_available(self):
        """
        Checks if there are any changes recorded in this ChangeManager instance

        :return: False if this ChangeManager instance is empty, otherwise True
        """
        return bool(len(self.change_sets))

    def was_this_an_expected_change(self, object, key, value):
        """
        Checks if a given change for a given object was recorded. If such a
        change was found, that change will also be removed from the list of
        recorded changes for given object.

        :param object: Object for which the change was recorded for
        :param key:    Key of the change
        :param value:  Value of the change
        :return:       False if change was not found, True if it was found
                       as well as removed
        """
        available_changes = self.get_changes(object)
        print("Beep: %s" % (available_changes))
        if available_changes:
            for c in list(available_changes):
                if c.check(key, value):
                    print(c)
                    self.remove_change(object, c)
                    return True

        return False
