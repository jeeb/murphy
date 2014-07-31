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
from threading import Event
from ws4py.client.threadedclient import WebSocketClient
import json


class InternalClient(WebSocketClient):
    def __init__(self, address, protocols):
        super(InternalClient, self).__init__(address, protocols=protocols)
        self.iclient_callback_set = False
        self.iclient_callback = None

    def received_message(self, message):
        if not self.iclient_callback_set:
            pass
        else:
            self.iclient_callback(message)

    def set_callback(self, func):
        if not callable(func):
            raise TypeError("Set checker function is not callable!")

        self.iclient_callback = func
        self.iclient_callback_set = True


class Status(object):
    def __init__(self):
        self.state = Event()
        self.result = None

    def ready(self):
        return self.state.is_set()

    def mark_ready(self):
        self.state.set()

    def get_result(self):
        if not self.state:
            pass
        else:
            return self.result

    def set_result(self, result):
        self.result = result
        self.mark_ready()

    def wait(self, timeout=None):
        return self.state.wait(timeout)


class MurphyConnection(object):
    def __init__(self, address):
        self.global_seq = 0
        self.queue = dict()

        self.client = InternalClient(address, protocols=["murphy"])
        self.client.set_callback(self.check)

        self.events = []

        self.own_sets = dict()

    def connect(self):
        self.client.connect()

    def disconnect(self):
        self.client.close()

    def daemonize(self, value=True):
        self.client.daemon = value

    def check(self, message):
        if message.is_text:
            message_data = json.loads(message.data.decode("utf-8"))
            seq = message_data.get("seq")
            type = message_data.get("type")

            if seq is None or type is None:
                print("E: Either sequence or type was not in the reply! (seq %s - type %s)" % (seq, type))
                return

            # Is this an event?
            if type == "event":
                print("D: Got an event! (seq %s - type %s)" % (seq, type))
                self.events.append(message_data)
                return
            # Is this a response to one of our messages?
            elif seq in self.queue:
                if type in self.queue.get(seq):
                    print("D: Got a response to a sent message! (seq %s - type %s)" % (seq, type))
                    self.queue.get(seq, {}).get(type).set_result(message_data)
                    return
            # If the message is neither, it's unrelated/unknown
            else:
                print("D: Got unrelated message (seq %s - type %s)" % (seq, type))
        else:
            print("D: Got le binary message!?")

    def check_for_events(self):
        if not self.events:
            return None

        # Grab the oldest event waiting for us
        oldest_event = self.events.pop(0)

        id = oldest_event.get("id")

        if id is None:
            print("E: No id found in the event!")
            return None

        if id in self.own_sets:
            print("D: We found an event for set %s" % (id))
            # Update the information in the set
            self.own_sets.get(id).update(oldest_event)
            print("D: %s" % (self.own_sets.get(id)))
            return True
        else:
            print("D: We found an event for a set that is not yet in our books (id = %s)" % (id))
            self.events.append(oldest_event)
            return None

    def add_to_queue(self, type, seq, status):
        if seq in self.queue:
            self.queue.get(seq)[type] = status
        else:
            self.queue[seq] = {type: status}

    def remove_from_queue(self, type, seq):
        print("D: queue = %s" % (self.queue))
        if seq in self.queue:
            if type in self.queue.get(seq):
                del(self.queue.get(seq)[type])
                if not self.queue.get(seq):
                    del(self.queue[seq])
                return True
            else:
                return False
        else:
            return False

    def give_seq_and_increment(self):
        current = self.global_seq
        self.global_seq += 1
        return current

    def send_msg(self, data_dict):
        # Initialize the status object and the current sequence number
        status = Status()
        local_seq = self.give_seq_and_increment()

        # Try getting the message type

        type = data_dict.get("type")
        if not type:
            print("E: Message type not found in message data!")
            return None

        # Add the message to response queue
        self.add_to_queue(type, local_seq, status)

        # Add the sequence to the data and send the actual message
        data_dict.update({"seq": local_seq})
        self.client.send(json.dumps(data_dict))

        # Wait for the response callback to be hit
        gatekeeper = status.wait(5.0)
        self.remove_from_queue(type, local_seq)

        # If gatekeeper tells us that we didn't get a response, we timed out
        if not gatekeeper:
            print("E: Timed out on the response (waited five seconds; seq %s - type %s)" % (local_seq, type))
            return None

        # Get the response data from the status object
        response = status.get_result()
        print("D: Response gotten %s" % (response))

        # Delete the status object itself
        del(status)

        return response

    def list_resources(self):
        base = {"type": "query-resources"}
        resources = []

        # We send the query-messages message, and get a response
        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Listing resources failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        for res in response.get("resources"):
            resources.append(res.get("name"))

        return resources

    def get_resource(self, name):
        base = {"type": "query-resources"}

        # We send the query-messages message, and get a response
        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Listing resources for getting a resource failed with errcode %s (%s) :<" %
                  (errcode, response.get("message")))
            return None

        # Return the data of the resource asked for
        resources = response.get("resources")
        for res in resources:
            if res.get("name") == name:
                return res

    def list_classes(self):
        base = {"type": "query-classes"}

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Listing application classes failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        return response.get("classes")

    def list_zones(self):
        base = {"type": "query-zones"}

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Listing zones failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        return response.get("zones")

    def create_set(self, app_class, zone, priority, resources):
        base = {"type": "create"}
        resource_data = []

        if not isinstance(resources, list):
            resources = [resources]

        # Construct the list of resource data
        for res in resources:
            resource_data.append(self.get_resource(res))

        # Put it all into a single structure
        base.update({"resources": resource_data})
        base.update({"class": app_class})
        base.update({"zone": zone})
        base.update({"priority": priority})

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Creating set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        # Create a new entry for the
        set = {response.get("id"): base}

        self.own_sets.update(set)
        print("D: Added a set: %s" % (self.own_sets))

        return response.get("id")

    def destroy_set(self, set_id):
        base = {"type": "destroy"}

        base.update({"id": set_id})

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Destroying a set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        return True

    def acquire_set(self, set_id):
        base = {"type": "acquire"}

        base.update({"id": set_id})

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Acquiring a set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        return True

    def release_set(self, set_id):
        base = {"type": "release"}

        base.update({"id": set_id})

        response = self.send_msg(base)
        if not response:
            print("E: Sending message or receiving reply failed")
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Releasing a set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            return None

        return True


if __name__ == "__main__":
    connection = MurphyConnection("ws://localhost:4000/murphy")
    connection.daemonize(False)
    connection.connect()

    resources = connection.list_resources()
    classes = connection.list_classes()
    zones = connection.list_zones()
    print(resources)
    print(classes)
    print(zones)

    set = connection.create_set(classes[0], zones[0], 0, resources[0])
    connection.check_for_events()

    connection.acquire_set(set)
    connection.check_for_events()

    connection.release_set(set)
    connection.check_for_events()

    if connection.destroy_set(set):
        print("The set was successfully destroyed")
    else:
        print("Failed to destroy the set")

    connection.disconnect()
