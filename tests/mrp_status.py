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

from threading import Event


class StatusQueue(object):
    def __init__(self):
        self._dict = dict()

    def add(self, msg_type, seq, status):
        """
        Add a message to the 'responses expected' queue

        :param msg_type: Type of message to add to queue
        :param seq:      Sequence ID of the message to add to queue
        :param status:   Status object for this queue entry
        """
        if seq in self._dict:
            self._dict.get(seq)[msg_type] = status
        else:
            self._dict[seq] = {msg_type: status}

    def remove(self, msg_type, seq):
        """
        Remove a message from the 'responses expected' queue

        :param msg_type: Type of message to remove from queue
        :param seq:      Sequence ID of the message to remove from queue
        :return:         False if message was not in queue, True if it was
        """
        print("D: queue = %s" % (self._dict))
        if seq in self._dict:
            if msg_type in self._dict.get(seq):
                del(self._dict.get(seq)[msg_type])
                if not self._dict.get(seq):
                    del(self._dict[seq])
                return True
            else:
                return False
        else:
            return False

    @property
    def contents(self):
        return self._dict


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
