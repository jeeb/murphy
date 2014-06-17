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


def create_array(dbus_array):
    ret = []
    for val in dbus_array:
        ret.append(dbus_type_to_py_type(val)(val))

    return ret


def dbus_type_to_py_type(val):
    return {
        dbus.String: str,
        dbus.Int32:  int,
        dbus.UInt32: int,
        dbus.Double: float,
        dbus.Array:  create_array,
        dbus.Dictionary: dbus.Dictionary,
        dbus.ObjectPath: str,
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

        self.cb_set    = None
        self.user_data = None

        def resource_internal_callback(prop, value):
            if self.cb_set:
                self.cb_set(prop, value, self, self.user_data)

        self.res_iface.connect_to_signal("propertyChanged", resource_internal_callback)

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
            attributes  = self.res_iface.getProperties()["attributes"]
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

    def register_callback(self, cb, user_data=None):
        if not callable(cb):
            raise TypeError

        self.cb_set = cb
        self.user_data = user_data

    def get_mainloop(self):
        return self.config.mainloop

    def pretty_print(self):
        return pretty_str_dbus_dict(self.res_iface.getProperties())


class ResourceSet(object):
    """
    The basic unit of acquiring and releasing resources. Resources can be acquired or lost independently if the
    configuration permits, but the client can only request and release whole resource sets.
    """
    def __init__(self, bus, config, set_path):
        """
        Initializes the created ResourceSet object.

        :param bus:      D-Bus Bus that was connected to in order to create this resource set.
        :param config:   DbusConfig object that contains the general configuration of the D-Bus connection.
        :param set_path: The path of the newly created resource set. Is automatically created when
                         Connection.create_resource_set() is called, which is the primary way of creating these
                         objects
        """
        self.set_path  = set_path
        self.bus       = bus
        self.config    = config
        self.set_id    = int(set_path.split("/")[-1])
        self.set_obj   = bus.get_object(config.bus_name, set_path)
        self.set_iface = dbus.Interface(self.set_obj, dbus_interface=MRP_RES_SET_IFACE)
        self.cb_set    = None
        self.user_data = None

        def res_set_internal_callback(prop, value):
            if self.cb_set:
                self.cb_set(prop, value, self, self.user_data)

        self.set_iface.connect_to_signal("propertyChanged", res_set_internal_callback)

    def list_available_resources(self):
        """
        Creates a list of the paths of available resources in this resource set.

        :return: List of the paths of resources in this resource set
        """
        res_list = []
        resources = self.set_iface.getProperties()["availableResources"]
        for resource in resources:
            res_list.append(str(resource))

        return res_list

    def add_resource(self, res):
        """
        Creates (adds) a resource to this resource set.

        :param res: Resource to add to the resource set
        :return:    None in case of failure, Resource object if successful

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(res, str):
            raise TypeError

        res_path = self.set_iface.addResource(res)
        if not res_path:
            return None

        return Resource(self.bus, self.config, res_path)

    @staticmethod
    def remove_resource(resource):
        """
        Removes (deletes) a resource from this resource set.

        :param resource: Resource object of the resource to remove
        :return:         Boolean that notes if the action was successful or not

        :raise TypeError: Causes and exception in case the given parameter is not a Resource object
        """
        if not isinstance(resource, Resource):
            raise TypeError

        return resource.delete()

    def request(self):
        """
        Requests the resource set for acquisition. Success here only means that the call succeeded,
        and actual results will be pushed through a D-Bus signal that you can register a callback for.

        :return: Boolean that notes if the action was successful or not
        """
        try:
            self.set_iface.request()
            return True
        except:
            return False

    def release(self):
        """
        Requests a release of the release set's resources. Success here only means that the call succeeded,
        and actual results will be pushed through a D-Bus signal that you can register a callback for.

        :return: Boolean that notes if the action was successful or not
        """
        try:
            self.set_iface.release()
            return True
        except:
            return False

    def get_state(self):
        """
        Returns the state of this resource set as a string

        :return: String that represents the last updated state of this resource set
                 * acquired
                 * available
                 * lost
                 * pending
                 * unknown
        """
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

    def register_callback(self, cb, user_data=None):
        if not callable(cb):
            raise TypeError

        self.cb_set = cb
        self.user_data = user_data

    def get_mainloop(self):
        return self.config.mainloop

    def pretty_print(self):
        return pretty_str_dbus_dict(self.set_iface.getProperties())


class Connection(object):
    """
    Connection to Murphy via D-Bus, can use either the session or system bus. Administrates the resource sets in the
    system. Primary configuration is done via the DbusConfig object fed when the object is constructed.
    """
    def __init__(self, config):
        """
        Initializes the created Connection object.

        :param config: DbusConfig object that contains the general configuration of the D-Bus connection.
        :return: Connection object created according to the given parameters
        """
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

        self.cb_set    = None
        self.user_data = None

        def connection_internal_callback(prop, value):
            if self.cb_set:
                self.cb_set(prop, value, self, self.user_data)

        self.interface.connect_to_signal("propertyChanged", connection_internal_callback)

    def create_resource_set(self):
        """
        Creates a resource set, which is the basic unit of acquiring and releasing resources. Resources can be
        acquired or lost independently if the configuration permits, but the client can only request and release
        whole resource sets.

        :return: None in case of failure, ResourceSet object if successful
        """
        set_path = self.interface.createResourceSet()
        if not set_path:
            return None

        return ResourceSet(self.bus, self.config, set_path)

    def list_resource_sets(self):
        """
        Creates a list of the paths of available resource sets in this D-Bus connection

        :return: List of the paths of resource sets in this D-Bus connection
        """
        res_sets = []
        listing = self.interface.getProperties()["resourceSets"]
        for path in listing:
            res_sets.append(str(path))

        return res_sets

    def get_resource_set(self, set_path):
        """
        Returns a ResourceSet object of the resource responds at the given path

        :param set_path: Path of the resource set to return
        :return:         None in case of failure, ResourceSet object if successful
        """
        if not isinstance(set_path, str):
            raise TypeError

        listing = self.interface.getProperties()["resourceSets"]
        if set_path in listing:
            return ResourceSet(self.bus, self.config, set_path)
        else:
            return None

    def register_callback(self, cb, user_data=None):
        """
        Registers a function to be called when a change occurs in this D-Bus connection. A Connection object administers
        resource sets, so this callback can be used to check for additions and removals of resource sets from the
        connection.

        :param cb:        Function to be called when a signal is received from Murphy via D-Bus. Must be callable.
                          Function will get the following parameters:
                          * Name of property (only "resourceSets" possible in case of a Connection object)
                          * Value of the property (list of paths of the resource sets under this Connection object)
                          * Object from which this signal callback was registered (Connection object)
                          * User data; Object given to this function passed on to the callback, or
                            None if one isn't set
        :param user_data: Object that will be passed on to the callback, or None if one isn't passed
        :return:          Void
        """
        if not callable(cb):
            raise TypeError

        self.cb_set = cb
        self.user_data = user_data

    def get_mainloop(self):
        """
        Returns the mainloop to which this object was created.

        :return: GObject mainloop (gobject.MainLoop)
        """
        return self.config.mainloop

    def pretty_print(self):
        """
        Returns the current contents of this object as received from D-Bus as a string

        :return: String that describes the current contents of this object as received from D-Bus
        """
        return pretty_str_dbus_dict(self.interface.getProperties())
