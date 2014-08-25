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


def connect():
    global connection

    connection = mrp.MurphyConnection(mrp.MRP_DEFAULT_ADDRESS)


def disconnect():
    global connection

    connection.close()
    connection = None


def list_classes():
    classes = connection.list_classes()
    assert classes is not None and classes

    return classes


def list_resources():
    resources = connection.list_resources()
    assert resources is not None and resources

    return resources


def list_zones():
    zones = connection.list_zones()
    assert zones is not None and zones

    return zones


def add_resource(name):
    res = connection.get_resource(name)
    assert res is not None

    return res


def build_set(resources, app_class, zone):
    res_set = mrp.ResourceSet()

    for res in resources:
        res_set.add_resource(res)

    set_id = connection.create_set(res_set, app_class, zone)
    assert set_id is not None

    return set_id


def destroy_set(set_id):
    assert connection.destroy_set(set_id)


def acquire_set(set_id):
    assert connection.acquire_set(set_id)


def release_set(set_id):
    assert connection.release_set(set_id)
