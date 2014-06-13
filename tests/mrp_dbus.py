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

MRP_MGR_IFACE     = "org.murphy.manager"
MRP_RES_SET_IFACE = "org.murphy.resourceset"
MRP_RES_IFACE     = "org.murphy.resource"


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


def dbus_type_to_py_type(val):
    return {
        dbus.String: str,
        dbus.Int32:  int,
        dbus.UInt32: int,
        dbus.Double: float,
    }.get(type(val))


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
    def __init__(self, bus, config, res_path):
        self.bus = bus
        self.config = config
        self.res_path = res_path
        self.res_id   = int(res_path.split("/")[-1])
        self.res_obj  = bus.get_object(config.bus_name, res_path)
        self.res_iface = dbus.Interface(self.res_obj, dbus_interface=MRP_RES_IFACE)

    def get_state(self):
        return str(self.res_iface.getProperties()["status"])

    def get_name(self):
        return str(self.res_iface.getProperties()["name"])

    def is_mandatory(self):
        return bool(self.res_iface.getProperties()["mandatory"])

    def make_mandatory(self, mandatory=True):
        if not isinstance(mandatory, bool):
            raise TypeError

        try:
            self.res_iface.setProperty("mandatory", dbus.Boolean(mandatory, variant_level=1))
            return True
        except:
            return False

    def is_shareable(self):
        return bool(self.res_iface.getProperties()["shared"])

    def make_shareable(self, shareable=True):
        if not isinstance(shareable, bool):
            raise TypeError

        try:
            self.res_iface.setProperty("shared", dbus.Boolean(shareable, variant_level=1))
            return True
        except:
            return False

    def list_attributes(self):
        attr_list = []
        attributes = self.res_iface.getProperties()["attributes"].keys()
        for attr in attributes:
            attr_list.append(str(attr))

        return attr_list

    def get_attribute_value(self, name):
        if not isinstance(name, str):
            raise TypeError

        attribute = self.res_iface.getProperties()["attributes"][name]
        cast = dbus_type_to_py_type(attribute)
        return cast(attribute)

    def set_attribute_value(self, name, value):
        try:
            attributes = self.res_iface.getProperties()["attributes"]
            if name in attributes:
                cast = type(attributes[name])
                attributes[name] = cast(value)

                self.res_iface.setProperty("attributes_conf", attributes)
                return True
            else:
                return False
        except dbus.DBusException:
            raise
        except:
            return False

    def delete(self):
        try:
            self.res_iface.delete()
            del(self)
            return True
        except:
            return False

    def register_cb_for_res_changes(self, cb, path_var_name):
        self.res_iface.connect_to_signal("propertyChanged", cb, path_keyword=path_var_name)

    def pretty_print(self):
        return pretty_str_dbus_dict(self.res_iface.getProperties())


class ResourceSet(object):
    def __init__(self, bus, config, set_path):
        self.set_path  = set_path
        self.bus       = bus
        self.config    = config
        self.set_id    = int(set_path.split("/")[-1])
        self.set_obj   = bus.get_object(config.bus_name, set_path)
        self.set_iface = dbus.Interface(self.set_obj, dbus_interface=MRP_RES_SET_IFACE)

    def list_available_resources(self):
        res_list = []
        resources = self.set_iface.getProperties()["availableResources"]
        for resource in resources:
            res_list.append(str(resource))

        return res_list

    def add_resource(self, res):
        if not isinstance(res, str):
            raise TypeError

        res_path = self.set_iface.addResource(res)
        if not res_path:
            return None

        return Resource(self.bus, self.config, res_path)

    @staticmethod
    def remove_resource(resource):
        if not isinstance(resource, Resource):
            raise TypeError

        return resource.delete()

    def request(self):
        try:
            self.set_iface.request()
            return True
        except:
            return False

    def release(self):
        try:
            self.set_iface.release()
            return True
        except:
            return False

    def get_state(self):
        return str(self.set_iface.getProperties()["status"])

    def get_class(self):
        return str(self.set_iface.getProperties()["class"])

    def set_class(self, app_class):
        if not isinstance(app_class, str):
            raise TypeError

        try:
            self.set_iface.setProperty("class", dbus.String(app_class, variant_level=1))
            return True
        except:
            return False

    def delete(self):
        try:
            self.set_iface.delete()
            return True
        except:
            return False

    def register_cb_for_res_set_changes(self, cb, path_var_name):
        self.set_iface.connect_to_signal("propertyChanged", cb, path_keyword=path_var_name)

    def pretty_print(self):
        return pretty_str_dbus_dict(self.set_iface.getProperties())


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
        self.interface = dbus.Interface(self.proxy, dbus_interface=MRP_MGR_IFACE)

    def create_resource_set(self):
        set_path = self.interface.createResourceSet()
        if not set_path:
            return None

        return ResourceSet(self.bus, self.config, set_path)

    def list_resource_sets(self):
        res_sets = []
        listing = self.interface.getProperties()["resourceSets"]
        for path in listing:
            res_sets.append(str(path))

        return res_sets

    def get_resource_set(self, set_path):
        if not isinstance(set_path, str):
            raise TypeError

        listing = self.interface.getProperties()["resourceSets"]
        if set_path in listing:
            return ResourceSet(self.bus, self.config, set_path)
        else:
            return None

    def register_cb_for_connection_changes(self, cb, path_var_name):
        self.interface.connect_to_signal("propertyChanged", cb, path_keyword=path_var_name)
