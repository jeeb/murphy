#!/usr/bin/env bash

if pidof "lt-murphyd" >/dev/null; then
    echo "Murphy is running, killing..."
    kill `pidof "lt-murphyd"`
    exit 0
else
    echo "Murphy not alive, exiting"
    exit 0
fi
