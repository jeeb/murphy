#!/usr/bin/env bash

if pidof "lt-murphyd" >/dev/null; then
    echo "Murphy is already running, exiting"
    exit 0
else
    echo "Murphy is not yet running, starting..."
    ../src/murphyd -P ../src/.libs -c conf/murphy-lua.conf -f -vv &
fi
