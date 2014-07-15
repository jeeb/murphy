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


def example_callback(prop, value, original_thing, user_data):
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
