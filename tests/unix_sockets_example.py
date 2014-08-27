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

import mrp_unix_sockets as mrp
from sys import argv

if __name__ == "__main__":
    thread = mrp.MurphyConnectionThread(mrp.MRP_DEFAULT_ADDRESS)

    conn = thread.mrp_conn

    resources = conn.list_resources()
    print(resources)

    classes = conn.list_classes()
    zones = conn.list_zones()
    print("\tAvailable Classes: %s" % (", ".join(str(x) for x in classes)))
    print("\tAvailable Zones: %s" % (", ".join(str(x) for x in zones)))

    res_set = mrp.ResourceSet()
    resource = conn.get_resource(resources[0])
    resource.mandatory = False

    res_set.add_resource(resource)
    res_set.add_resource(conn.get_resource(resources[1]))

    set_id = conn.create_set(res_set, classes[0], zones[0])
    conn.release_set(set_id)
    conn.acquire_set(set_id)

    if len(argv) > 1 and argv[1] == "listen":
        try:
            while True:
                if conn.parse_received_events():
                    print(conn.get_state(set_id).pretty_print())
        except KeyboardInterrupt:
            pass

    conn.release_set(set_id)
    conn.destroy_set(set_id)

    thread.close()
