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
from dbus.mainloop.glib import DBusGMainLoop
import gobject

manager_iface  = "org.murphy.manager"
res_set_iface  = "org.murphy.resourceset"
resource_iface = "org.murphy.resource"

# Ismo's pretty printing functions
def pretty_str_dbus_value(val, level=0, suppress=False):
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
    prefix = level * "\t"
    s = "[\n"
    for v in arr:
        s += pretty_str_dbus_value(v, level+1)
        s += "\n"
    s += prefix + "]"
    return s

def pretty_str_dbus_dict(d, level=0):
    prefix = level * "\t"
    s = "{\n"
    for k, v in d.items():
        s += prefix + "\t"
        s += str(k) + ": "
        s += pretty_str_dbus_value(v, level+1, True)
        s += "\n"
    s += prefix + "}"
    return s


class DbusConfig(object):
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.mainloop = gobject.MainLoop()
        self.bus_type = "session"
        self.bus_name = "org.Murphy"
        self.object_path = "/org/murphy/resource"

    def set_bus_type(self, bus_type):
        if bus_type != "session" or bus_type != "system":
            raise ValueError

        self.bus_type = bus_type

    def set_name(self, name):
        if not isinstance(name, str):
            raise TypeError

        self.bus_name = name

    def set_object_path(self, path):
        if not isinstance(path, str):
            raise TypeError

        self.object_path = path

class Resource(object):
    def __init__(self, bus, res_path):
        self.bus = bus
        self.res_path = res_path
        self.res_id   = int(res_path.split("/")[-1])
        self.res_obj  = bus.get_object("org.Murphy", res_path)
        self.res_iface = dbus.Interface(self.res_obj, dbus_interface=resource_iface)


class ResourceSet(object):
    def __init__(self, bus, set_path):
        self.set_path  = set_path
        self.bus       = bus
        self.set_id    = int(set_path.split("/")[-1])
        self.set_obj   = bus.get_object('org.Murphy', set_path)
        self.set_iface = dbus.Interface(self.set_obj, dbus_interface=res_set_iface)

    def list_available_resources(self):
        res_list = []
        props = self.set_iface.getProperties()
        for key, v in props.items():
            if str(key) == "availableResources":
                for val in v:
                    res_list.append(str(val))

        return res_list

    def add_resource(self, res):
        res_path = self.set_iface.addResource(res)
        if not res_path:
            return None

        return Resource(self.bus, res_path)

    def request(self):
        try:
            self.set_iface.request()
            return True
        except:
            return False

    # TODO: Actually find out how you list the application classes
    def list_application_classes(self):
        app_classes = []
        classes = self.set_iface.getProperties()[""]

    def get_class(self):
        return str(self.set_iface.getProperties()["class"])

    def set_class(self, app_class):
        try:
            self.set_iface.setProperty("class", dbus.String(app_class, variant_level=1))
            return True
        except:
            return False


class Connection(object):
    def __init__(self, config):
        if not isinstance(config, DbusConfig):
            raise TypeError

        self.config = config
        self.bus = None
        self.proxy = None
        self.interface = None

        # Select and initialize the selected dbus bus
        if config.bus_type == "session":
            self.bus = dbus.SessionBus()
        elif config.bus_type == "system":
            self.bus = dbus.SystemBus()

        if not self.bus:
            raise ValueError

        self.proxy = self.bus.get_object(self.config.bus_name, self.config.object_path)
        self.interface = dbus.Interface(self.proxy, dbus_interface=manager_iface)

    def create_resource_set(self):
        set_path = self.interface.createResourceSet()
        if not set_path:
            return None

        return ResourceSet(self.bus, set_path)

    def list_resource_sets(self):
        res_sets = []
        listing = self.interface.getProperties()["resourceSets"]
        for path in listing:
            res_sets.append(str(path))

        return res_sets



if __name__ == "__main__":
    conn = Connection(DbusConfig())
    res_set = conn.create_resource_set()
    if not res_set.set_class("player"):
        print("Perkele")
    res = res_set.add_resource(res_set.list_available_resources()[0])
    if not res_set.request():
        print("Perkele2")
    print(pretty_str_dbus_dict(res_set.set_iface.getProperties()))
