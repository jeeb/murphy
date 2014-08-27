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

from mrp_websockets import MurphyConnection

connection = None
local_resources = []
local_classes = []
local_zones = []

added_resources = []

set_id = None


def connect():
    global connection

    connection = MurphyConnection("ws://localhost:4000/murphy")
    connection.daemonize(False)
    connection.connect()


def disconnect():
    global connection

    connection.disconnect()
    connection = None


def list_classes():
    global local_classes
    local_classes = connection.list_classes()
    assert local_classes is not None and local_classes


def list_resources():
    global local_resources, added_resources
    local_resources = connection.list_resources()
    added_resources = []
    assert local_resources is not None and local_resources


def list_zones():
    global local_zones
    local_zones = connection.list_zones()
    assert local_zones is not None and local_zones


def add_resource(num):
    res = connection.get_resource(local_resources[num - 1])
    assert res is not None

    added_resources.append(res)


def remove_resource(num):
    name = local_resources[num - 1]

    for res in list(added_resources):
        if res.name == name:
            added_resources.remove(res)
            return


def build_set():
    global set_id
    set_id = connection.create_set(local_classes[0], local_zones[0], 0, added_resources)
    assert set_id is not None


def destroy_set():
    global set_id
    assert connection.destroy_set(set_id)
    set_id = None


def acquire_set():
    assert connection.acquire_set(set_id)


def release_set():
    assert connection.release_set(set_id)
