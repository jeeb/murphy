#!/usr/bin/env bash

if pidof "lt-murphyd" >/dev/null; then
    echo "Murphy is already running, exiting"
    exit 0
else
    echo "Murphy is not yet running, starting..."
    ../src/murphyd -P ../src/.libs -c conf/murphy-lua.conf -vv &
    # -V --leak-check=full --track-origins=yes --trace-children=yes
    # Murphy does not yet release a signal that it has finished starting
    # and thus we sleep
    sleep 1
fi
