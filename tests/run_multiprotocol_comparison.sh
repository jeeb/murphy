#!/usr/bin/env bash

ACTIONS=`fmbt -o adapter=dummy test_mrp_dbus.conf 2>/dev/null | fmbt-log -f '$ax'`
fmbt -i test_mrp_dbus.conf <<< "${ACTIONS}"
fmbt -i test_mrp_resource.conf <<< "${ACTIONS}"
# printf '%s' "${ACTIONS}" | fmbt -i test_mrp_dbus.conf

echo ${PIPESTATUS[@]}
