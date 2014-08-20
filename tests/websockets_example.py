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

from __future__ import unicode_literals
import sys
from mrp_websockets import MurphyConnection

if __name__ == "__main__":
    connection = MurphyConnection("ws://localhost:4000/murphy")
    connection.daemonize(False)
    connection.connect()

    resources = connection.list_resources()
    classes = connection.list_classes()
    zones = connection.list_zones()

    if resources is None or classes is None or zones is None:
        print("WebSocketExample: System information queries failed :<")
        sys.exit(1)

    print("WebSocketExample: System Dump")
    print("\tAvailable Resources: %s" % (", ".join(str(x) for x in resources)))
    print("\tAvailable Classes: %s" % (", ".join(str(x) for x in classes)))
    print("\tAvailable Zones: %s" % (", ".join(str(x) for x in zones)))

    # Grab a Resource
    resource = connection.get_resource(resources[0])

    # Change the flags around
    resource.optional = True
    resource.optional = False

    resource.shared = True
    resource.shared = False

    # Grab the attributes and modify them
    attributes = resource.attributes
    attributes.update({"role": "delivery"})

    # Finally, try and create a set with the resource (you can also create it with a list of Resources)
    r_set = connection.create_set(classes[0], zones[0], 0, resource)
    if r_set is None:
        print("WebSocketExample: Set creation failed :<")
        sys.exit(1)
    print("WebSocketExample: Set %s was created!" % (r_set))

    if connection.acquire_set(r_set):
        print("WebSocketExample: Set %s was successfully acquired!" % (r_set))
    else:
        print("WebSocketExample: Set %s was unsuccessfully acquired!" % (r_set))

    print("WebSocketExample: Set state now: %s" % connection.get_state(r_set))

    if len(sys.argv) > 1 and sys.argv[1] == "listen":
        try:
            while True:
                if connection.parse_received_events():
                    print(connection.get_state(r_set))
        except KeyboardInterrupt:
            pass

    if connection.release_set(r_set):
        print("WebSocketExample: Set %s was successfully released!" % (r_set))
    else:
        print("WebSocketExample: Set %s was unsuccessfully released!" % (r_set))

    print("WebSocketExample: Set state now: %s" % connection.get_state(r_set))

    if connection.destroy_set(r_set):
        print("The set was successfully destroyed")
    else:
        print("Failed to destroy the set")

    connection.disconnect()
