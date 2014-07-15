#!/usr/bin/env bash

TEST_CONFS=( "test_mrp_dbus.conf" "test_mrp_resource.conf" )
ACTIONS=`fmbt -o adapter=dummy test_mrp_dbus.conf 2>/dev/null | fmbt-log -f '$ax'`

run_test()
{
test_name=${1}
    fmbt -i "${test_name}" <<< "${ACTIONS}" 2> >(grep -v "ignoring malformed resource event" 1> "${test_name%.*}_test_run.log")
}

for i in "${TEST_CONFS[@]}"
do
    run_test "$i"
done

diff -u *_test_run.log
exit $?
