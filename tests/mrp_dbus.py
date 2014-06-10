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

class DbusConfig(object):
    def __init__(self):
        self.bus_type = "session"
        self.bus_name = "org.Murphy"
        self.object_path = "/org/murphy/resource"
        self.iface_name  = "org.murphy.manager"

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

    def set_iface_name(self, name):
        if not isinstance(name, str):
            raise TypeError

        self.iface_name = name


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
        self.interface = dbus.Interface(self.proxy, dbus_interface=self.config.iface_name)



if __name__ == "__main__":
    conn = Connection(DbusConfig())
    print(conn)
