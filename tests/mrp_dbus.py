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

# Murphy D-Bus interface names
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


class DBusConfig(object):
    """
    Object containing the various configuration options for the D-Bus connection, including its type (session/system),
    the bus name as well as the object path and mainloop
    """
    def __init__(self):
        """
        Initializes the created DBusConfig object. Defaults for all values are set by default.
        """
        DBusGMainLoop(set_as_default=True)
        self.mainloop = gobject.MainLoop()
        self.bus_type = "system"
        self.bus_name = "org.Murphy"
        self.object_path = "/org/murphy/resource"

    def set_bus_type(self, bus_type):
        """
        Sets the D-Bus bus type to be connected to

        :param bus_type: String that represents the bus type to selected

        :raise ValueError: Causes an exception in case the given parameter is not one of "session" or "system"
        """
        if bus_type != "session" and bus_type != "system":
            raise ValueError

        self.bus_type = bus_type

    def set_name(self, name):
        """
        Sets the bus name to be used when connecting

        :param name: String that represents the bus name

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(name, str):
            raise TypeError

        self.bus_name = name

    def set_object_path(self, path):
        """
        Sets the object path to the used managing interface

        :param path: String that represents the object path

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(path, str):
            raise TypeError

        self.object_path = path

    def reset_mainloop(self):
        """
        Recreates the mainloop to which this object was created. If the
        mainloop is still running, it will quit it and create a new one that you can
        then later start again.

        :return: Void
        """
        if self.mainloop:
            if self.mainloop.is_running():
                self.mainloop.quit()

            del(self.mainloop)

        self.mainloop = gobject.MainLoop()


class Resource(object):
    """
    Object signifying a single resource in a resource set. Depending on the configuration not all resources are always
    acquired when a resource set is acquired (non-mandatory resources).

    Resources, as well as resource sets can not be modified via the API after they have been acquired, to modify values
    one must first successfully release the resource set, modify a given value, and then re-acquire it.
    """
    def __init__(self, res_set, res_name=None, given_path=None):
        """
        Initializes the created Resource object. Needs one of the two optional parameters to be set for either
        resource addition or for getting an already added resource.

        :param res_set:    Murphy ResourceSet object that this resource is to be created under.
        :param res_name:   Optional resource name parameter used when a new resource is to be added
        :param given_path: Optional D-Bus object path parameter used when an already existing resource is to be used
        """

        # You're not supposed to use both optional parameters at once
        if res_name and given_path:
            raise ValueError

        # If we're given a path, we're grabbing an already existing resource
        if given_path:
            self.res_path = given_path
        # Otherwise create a new resource with the given name
        else:
            self.res_path = res_set.set_iface.addResource(res_name)

        if not self.res_path:
            raise ValueError

        self.bus = res_set.bus
        self.config = res_set.config
        self.res_id   = int(self.res_path.split("/")[-1])
        self.res_obj  = self.bus.get_object(self.config.bus_name, self.res_path)
        self.res_iface = dbus.Interface(self.res_obj, dbus_interface=MRP_RES_IFACE)

        self.cb_set    = None
        self.user_data = None

        def resource_internal_callback(prop, value):
            if self.cb_set:
                self.cb_set(prop, value, self, self.user_data)

        self.int_callback = resource_internal_callback

    def get_state(self):
        """
        Returns the state of this resource as a string

        :return: String that represents the last updated state of this resource
                 * acquired
                 * available
                 * lost
                 * pending
                 * unknown
        """
        return str(self.res_iface.getProperties()["status"])

    def get_name(self):
        """
        Returns the name of this resource as a string

        :return: String that represents the name of this resource in the system
        """
        return str(self.res_iface.getProperties()["name"])

    def is_mandatory(self):
        """
        Returns if this resource is mandatory for the resource set acquisition to succeed

        :return: Boolean that notes if the resource is required for the acquisition of the resource set
        """
        return bool(self.res_iface.getProperties()["mandatory"])

    def make_mandatory(self, mandatory=True):
        """
        Sets the mandatory state for this resource

        :param mandatory: Optional parameter that notes the value for the state to be set, True if unset
        :return:          Boolean that notes if the action was successful or not

        :raise TypeError: Causes an exception in case the given parameter is not a boolean
        """
        if not isinstance(mandatory, bool):
            raise TypeError

        try:
            self.res_iface.setProperty("mandatory", dbus.Boolean(mandatory, variant_level=1))
            return True
        except:
            return False

    def is_shareable(self):
        """
        Returns if this resource is shareable between multiple clients

        :return: Boolean that notes if the resource is shareable between multiple clients
        """
        return bool(self.res_iface.getProperties()["shared"])

    def make_shareable(self, shareable=True):
        """
        Sets the shareable state for this resource

        :param shareable: Optional parameter that notes the value of the state to be set, True if unset
        :return:          Boolean that notes if the action was successful or not

        :raise TypeError: Causes an exception in case the given parameter is not a boolean
        """
        if not isinstance(shareable, bool):
            raise TypeError

        try:
            self.res_iface.setProperty("shared", dbus.Boolean(shareable, variant_level=1))
            return True
        except:
            return False

    def list_attribute_names(self):
        """
        Creates a list of the available attributes in this resource

        :return: List that contains the names of the attributes available in this resource
        """
        attr_list = []
        attributes = self.res_iface.getProperties()["attributes"].keys()
        for attr in attributes:
            attr_list.append(str(attr))

        return attr_list

    def get_attribute_value(self, name):
        """
        Returns the value of an attribute from this resource by name

        :param name: Name of the attribute the value of which will be returned
        :return:     Value of the attribute the name of which was passed as the parameter

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(name, str):
            raise TypeError

        attribute = self.res_iface.getProperties()["attributes"][name]
        return attribute

    def get_attribute_type(self, name):
        """
        Returns the type of a value of an attribute from this resource by name

        :param name: Name of the attribute
        :return:     Type of the given attribute value

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(name, str):
            raise TypeError

        attribute = self.res_iface.getProperties()["attributes"][name]
        return type(attribute)

    def set_attribute_value(self, name, value):
        """
        Sets a specific attribute to a given value

        :param name:  Name of the attribute the value of which will be set
        :param value: Value to be set for the attribute
        :return:      Boolean that notes if the action was successful or not

        :raise: Causes an exception in case a DBusException was thrown
        """
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
        """
        Deletes (removes) the resource from its resource set

        :return: Boolean that notes if the action was successful or not
        """
        try:
            self.res_iface.delete()
            del(self)
            return True
        except:
            return False

    def register_callback(self, cb, user_data=None):
        """
        Registers a function to be called when a change occurs in this D-Bus connection regarding this resource.

        :param cb:        Function to be called when a signal is received from Murphy via D-Bus. Must be callable.
                          Function will get the following parameters:
                          * Name of property
                            * status
                            * name
                            * mandatory
                            * shared
                            * attributes      (attributes with currently set values)
                            * attributes_conf (attributes with values to propagate)
                          * Value of the property
                          * Object from which this signal callback was registered (Resource object)
                          * User data; Object given to this function passed on to the callback, or
                            None if one isn't set
        :param user_data: Object that will be passed on to the callback, or None if one isn't passed

        :raise TypeError: Causes an exception in case the given parameter is not callable
        """
        if not callable(cb):
            raise TypeError

        self.cb_set = cb
        self.user_data = user_data

        self.res_iface.connect_to_signal("propertyChanged", self.int_callback)

    def get_mainloop(self):
        """
        Returns the mainloop to which this object was created.

        :return: GObject mainloop (gobject.MainLoop)
        """
        return self.config.mainloop

    def get_path(self):
        """
        Returns the object path of this resource. Can be useful in callbacks, for example

        :return: String representation of the object path of this resource set
        """
        return self.res_path

    def pretty_print(self):
        """
        Returns the current contents of this object as received from D-Bus as a string

        :return: String that describes the current contents of this object as received from D-Bus
        """
        return pretty_str_dbus_dict(self.res_iface.getProperties())


class ResourceSet(object):
    """
    The basic unit of acquiring and releasing resources. Resources can be acquired or lost independently if the
    configuration permits, but the client can only request and release whole resource sets.

    Resource sets and their resources can only be generally modified until they are acquired. Any changes done
    after acquisition will currently end in failure.
    """
    def __init__(self, conn, given_path=None):
        """
        Initializes the created ResourceSet object.

        :param conn:       Murphy Connection object that this resource set is to be created under.
        :param given_path: Optional D-Bus object path to an existing resource set.
        """

        # If we're given a path, we're grabbing an already existing resource set
        if given_path:
            self.set_path = given_path
        # Otherwise create the resource set
        else:
            self.set_path  = conn.interface.createResourceSet()

        if not self.set_path:
            raise ValueError

        self.bus       = conn.bus
        self.config    = conn.config
        self.set_id    = int(self.set_path.split("/")[-1])
        self.set_obj   = self.bus.get_object(self.config.bus_name, self.set_path)
        self.set_iface = dbus.Interface(self.set_obj, dbus_interface=MRP_RES_SET_IFACE)
        self.cb_set    = None
        self.user_data = None

        def res_set_internal_callback(prop, value):
            if self.cb_set:
                self.cb_set(prop, value, self, self.user_data)

        self.int_callback = res_set_internal_callback

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

        return Resource(self, res_name=res)

    def list_resources(self):
        """
        Creates a list of the paths of currently added resources in this resource set.

        :return: List of the object paths of currently added resources in this resource set
        """
        res_list = []
        resources = self.set_iface.getProperties()["resources"]
        for resource in resources:
            res_list.append(resource)

        return res_list

    def get_resource(self, obj_path):
        """
        Returns a Resource object of the resource described by the given object path

        :param obj_path: D-Bus object path describing a specific Murphy resource
        :return:         None in case of failure, Resource object if successful
        """
        resources = self.set_iface.getProperties()["resources"]
        if obj_path in resources:
            return Resource(self, given_path=obj_path)
        else:
            return None

    @staticmethod
    def remove_resource(resource):
        """
        Removes (deletes) a resource from this resource set.

        :param resource: Resource object of the resource to remove
        :return:         Boolean that notes if the action was successful or not

        :raise TypeError: Causes an exception in case the given parameter is not a Resource object
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
        """
        Returns the class of this resource set as a string

        :return: String that represents the set class of this resource set
        """
        return str(self.set_iface.getProperties()["class"])

    def set_class(self, app_class):
        """
        Sets the class of this resource set.

        :param app_class: String representation of the class to be set for this resource set
        :return:          Boolean that notes if the action was successful or not

        :raise TypeError: Causes an exception in case the given parameter is not a string
        """
        if not isinstance(app_class, str):
            raise TypeError

        try:
            self.set_iface.setProperty("class", dbus.String(app_class, variant_level=1))
            return True
        except:
            return False

    def delete(self):
        """
        Deletes the resource set from the system

        :return: Boolean that notes if the action was successful or not
        """
        try:
            self.set_iface.delete()
            return True
        except:
            return False

    def register_callback(self, cb, user_data=None):
        """
        Registers a function to be called when a change occurs in this D-Bus connection regarding this resource set.
        This does include addition and removal of resources to/from this resource set, but changes in resources
        included in this resources are handled by their own signals.

        :param cb:        Function to be called when a signal is received from Murphy via D-Bus. Must be callable.
                          Function will get the following parameters:
                          * Name of property
                            * class
                            * status
                            * availableResources
                            * resources
                          * Value of the property
                          * Object from which this signal callback was registered (ResourceSet object)
                          * User data; Object given to this function passed on to the callback, or
                            None if one isn't set
        :param user_data: Object that will be passed on to the callback, or None if one isn't passed

        :raise TypeError: Causes an exception in case the given callback function is not callable
        """
        if not callable(cb):
            raise TypeError

        self.cb_set = cb
        self.user_data = user_data

        self.set_iface.connect_to_signal("propertyChanged", self.int_callback)

    def get_mainloop(self):
        """
        Returns the mainloop to which this object was created.

        :return: GObject mainloop (gobject.MainLoop)
        """
        return self.config.mainloop

    def get_path(self):
        """
        Returns the object path of this resource set. Can be useful in callbacks, for example

        :return: String representation of the object path of this resource set
        """
        return self.set_path

    def pretty_print(self):
        """
        Returns the current contents of this object as received from D-Bus as a string

        :return: String that describes the current contents of this object as received from D-Bus
        """
        return pretty_str_dbus_dict(self.set_iface.getProperties())


class Connection(object):
    """
    Connection to Murphy via D-Bus, can use either the session or system bus. Administrates the resource sets in the
    system. Primary configuration is done via the DBusConfig object fed when the object is constructed.
    """
    def __init__(self, config):
        """
        Initializes the created Connection object.

        :param config: DBusConfig object that contains the general configuration of the D-Bus connection.
        :return: Connection object created according to the given parameters
        """
        if not isinstance(config, DBusConfig):
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

        self.int_callback = connection_internal_callback

    def create_resource_set(self):
        """
        Creates a resource set, which is the basic unit of acquiring and releasing resources. Resources can be
        acquired or lost independently if the configuration permits, but the client can only request and release
        whole resource sets.

        :return: None in case of failure, ResourceSet object if successful
        """
        return ResourceSet(self)

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
            return ResourceSet(self, set_path)
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

        self.interface.connect_to_signal("propertyChanged", self.int_callback)

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
