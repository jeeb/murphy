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
        """
        Simple WebSocketClient that lets you set the callback with a function

        :param address:   WebSocket (ws/wss/ws+sock) address to which to connect
        :param protocols: A list of protocols that you speak
        """
        super(InternalClient, self).__init__(address, protocols=protocols)
        self.iclient_callback_set = False
        self.iclient_callback = None

    def received_message(self, message):
        """
        Called when the underlying WebSocketClient implementation receives a message,
        calls a callback function if set

        :param message: Instance of ws4py.messaging.Message received
        """
        if not self.iclient_callback_set:
            pass
        else:
            self.iclient_callback(message)

    def set_callback(self, func):
        """
        Sets the callback to a function of your choice

        :param func: A callable that you wish to set as the callback
        :raises TypeError if the object you provided is not callable
        """
        if not callable(func):
            raise TypeError("Set checker function is not callable!")

        self.iclient_callback = func
        self.iclient_callback_set = True


class Status(object):
    def __init__(self):
        """
        Status object that can contain a result (object) and has an Event built in
        """
        self.state = Event()
        self.result = None

    def ready(self):
        """
        Queries if the state of this Status object is that its ready

        :return: True or False depending on the Status object's state
        """
        return self.state.is_set()

    def mark_ready(self):
        """
        Marks this Status object as ready - everything waiting for it will stop blocking

        :return: Void
        """
        self.state.set()

    def get_result(self):
        """
        Returns the object stored in this Status object
        :return: None, or object that is stored in this Status object
        """
        if not self.state:
            pass
        else:
            return self.result

    def set_result(self, result):
        """
        Sets the object to be stored in this Status object

        :param result: Object to be stored in this Status object
        :return:       Void
        """
        self.result = result
        self.mark_ready()

    def wait(self, timeout=None):
        """
        Blocks until this Status object is ready.

        :param timeout: Floating point value that defines how many seconds this Status object will
                        block in case it is not yet ready.
        :return:        Returns a boolean state of whether or not this State object was ready when it
                        stopped blocking; This can be used to check whether or not this call timed out.
        """
        return self.state.wait(timeout)


# FIXME: This will not be needed when we switch from list to dict for resources
def update_resources(old_res, new_res):
    for res in new_res:
        for ores in old_res:
            if ores.get("name") == res.get("name"):
                mask = ores.get("mask")
                ores = res
                ores.update({"mask": mask})
                break

    return old_res


class Resource(object):
    def __init__(self, resource_data):
        self.res_structure = resource_data
        self.res_structure.update({"flags": list()})

    @property
    def shared(self):
        return bool(self.res_structure.get("flags").count("shared"))

    @shared.setter
    def shared(self, flag):
        if flag:
            if self.res_structure.get("flags").count("shared"):
                return
            else:
                self.res_structure.get("flags").append("shared")
        else:
            try:
                self.res_structure.get("flags").remove("shared")
            except ValueError:
                return

    @property
    def optional(self):
        return bool(self.res_structure.get("flags").count("optional"))

    @optional.setter
    def optional(self, flag):
        if flag:
            if self.res_structure.get("flags").count("optional"):
                return
            else:
                self.res_structure.get("flags").append("optional")
        else:
            try:
                self.res_structure.get("flags").remove("optional")
            except ValueError:
                return

    @property
    def attributes(self):
        return self.res_structure.get("attributes")

    @property
    def internals(self):
        return self.res_structure


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
                if seq in self.queue and type in self.queue.get(seq):
                    print("D: Got an event that is a response to a sent message!")
                    self.queue.get(seq, {}).get(type).set_result(message_data)
                    return
                else:
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


    def parse_event(self, event):
        id = event.get("id")
        if id is None:
            print("E: No id found in the event!")
            return None

        if id in self.own_sets:
            print("D: We found an event for set %s" % (id))
            # Update the resources to the updated set separately, as otherwise we lose information
            # that is no longer transferred to us (such as the bitmask)
            event["resources"] = update_resources(self.own_sets.get(id).get("resources"),
                                                  event.get("resources"))
            # Update the information in the set
            self.own_sets.get(id).update(event)
            print("D: %s" % (self.own_sets.get(id)))
            return True
        else:
            print("D: We found an event for a set that is not yet in our books (id = %s)" % (id))
            return False


    def parse_received_events(self):
        if not self.events:
            return None

        for event in list(self.events):
            result = self.parse_event(event)

            # Either the event was invalid or a set was updated with its information,
            # remove the event from the list
            if result is None or result:
                self.events.remove(event)
            # Otherwise we just keep iterating

        return True

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

    def send_msg(self, data_dict, seq_num=None):
        # Initialize the status object and the current sequence number
        status = Status()

        local_seq = seq_num
        if local_seq is None:
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
                return Resource(res)

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
        status = Status()

        if not isinstance(resources, list):
            resources = [resources]

        # Construct the list of resource data
        for res in resources:
            resource_data.append(res.internals)

        # Put it all into a single structure
        base.update({"resources": resource_data})
        base.update({"class": app_class})
        base.update({"zone": zone})
        base.update({"priority": priority})

        # We need to know the sequence id, so we grab it here already
        local_seq = self.give_seq_and_increment()

        # Add the expected event to the queue
        self.add_to_queue("event", local_seq, status)

        # Send the query message out with known sequence id
        response = self.send_msg(base, seq_num=local_seq)
        if not response:
            print("E: Sending message or receiving reply failed")
            self.remove_from_queue("event", local_seq)
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Creating set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            self.remove_from_queue("event", local_seq)
            return None

        gatekeeper = status.wait(5.0)
        self.remove_from_queue("event", local_seq)

        if not gatekeeper:
            print("E: Timed out on the acquisition response event (waited five seconds")
            return None

        # Create a new entry for the
        set = {response.get("id"): status.get_result()}

        # Add the new set to the listing
        self.own_sets.update(set)
        print("D: Added a set: %s" % (self.own_sets.get(response.get("id"))))

        del(status)

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
        status = Status()

        base.update({"id": set_id})

        # We need to know the sequence id, so we grab it here already
        local_seq = self.give_seq_and_increment()

        # Add the expected event to the queue
        self.add_to_queue("event", local_seq, status)

        # Send the query message out with known sequence id
        response = self.send_msg(base, seq_num=local_seq)
        if not response:
            print("E: Sending message or receiving reply failed")
            self.remove_from_queue("event", local_seq)
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Acquiring a set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            self.remove_from_queue("event", local_seq)
            return None

        gatekeeper = status.wait(5.0)
        self.remove_from_queue("event", local_seq)

        if not gatekeeper:
            print("E: Timed out on the acquisition response event (waited five seconds")
            return None

        # Update the resources to the updated set separately, as otherwise we lose information
        # that is no longer transferred to us (such as the bitmask)
        status.get_result()["resources"] = update_resources(self.own_sets.get(set_id).get("resources"),
                                                            status.get_result().get("resources"))
        self.own_sets.get(set_id).update(status.get_result())
        print("D: Acquired a resource set and the state was updated to: %s" % (self.own_sets.get(set_id)))

        del(status)
        return True

    def release_set(self, set_id):
        base = {"type": "release"}
        status = Status()

        base.update({"id": set_id})

        # We need to know the sequence id, so we grab it here already
        local_seq = self.give_seq_and_increment()

        # Add the expected event to the queue
        self.add_to_queue("event", local_seq, status)

        # Send the query message out with known sequence id
        response = self.send_msg(base, seq_num=local_seq)
        if not response:
            print("E: Sending message or receiving reply failed")
            self.remove_from_queue("event", local_seq)
            return None

        # Status is C-like, zero is OK and nonzero are failure states
        errcode = response.get("error")
        if errcode:
            print("E: Releasing a set failed with errcode %s (%s) :<" % (errcode, response.get("message")))
            self.remove_from_queue("event", local_seq)
            return None

        gatekeeper = status.wait(5.0)
        self.remove_from_queue("event", local_seq)

        if not gatekeeper:
            print("E: Timed out on the release response event (waited five seconds")
            return None

        # Update the resources to the updated set separately, as otherwise we lose information
        # that is no longer transferred to us (such as the bitmask)
        status.get_result()["resources"] = update_resources(self.own_sets.get(set_id).get("resources"),
                                                            status.get_result().get("resources"))
        self.own_sets.get(set_id).update(status.get_result())
        print("D: Released a resource set and the state was updated to: %s" % (self.own_sets.get(set_id)))

        del(status)
        return True

    def get_state(self, set_id):
        set = self.own_sets.get(set_id)
        state = dict()

        set_acquisition_state = set.get("grant")
        state["acquired"] = bool(set_acquisition_state)
        state["resources"] = dict()

        for res in set.get("resources"):
            res_name = res.get("name")

            # Create the dictionary for the in-resource data
            state.get("resources")[res_name] = dict()

            # Grab the newly created resource dictionary and add things to it
            dict_res = state.get("resources").get(res_name)
            dict_res["acquired"] = bool(set_acquisition_state & res.get("mask"))
            dict_res["attributes"] = res.get("attributes")

        return state
