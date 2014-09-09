if FMBT_AVAILABLE

TESTS = run_murphyd.sh
NEEDED_LOGS = run_murphyd.log

# Actual tests requiring Murphy begin

if BUILD_RESOURCES
TESTS += test_mrp_libresource.conf
test_mrp_libresource.log: run_murphyd.log
NEEDED_LOGS += test_mrp_libresource.log

TESTS += test_mrp_libresource_dbuslike.conf
test_mrp_libresource_dbuslike.log: run_murphyd.log
NEEDED_LOGS += test_mrp_libresource_dbuslike.log

TESTS += test_mrp_unix_sockets.conf
test_mrp_resource_native.log: run_murphyd.log
NEEDED_LOGS += test_mrp_unix_sockets.log
endif

if DBUS_ENABLED
TESTS += test_mrp_dbus.conf
test_mrp_dbus.log: run_murphyd.log
NEEDED_LOGS += test_mrp_dbus.log
endif

if WEBSOCKETS_ENABLED
if WS4PY_AVAILABLE
TESTS += test_mrp_websockets.conf
test_mrp_websockets.log: run_murphyd.log
NEEDED_LOGS += test_mrp_websockets.log
endif
endif

if BUILD_RESOURCES
if DBUS_ENABLED
TESTS += run_multiprotocol_comparison.sh
run_multiprotocol_comparison.log: run_murphyd.log
NEEDED_LOGS += run_multiprotocol_comparison.log
endif
endif

if DBUS_ENABLED
TESTS += dbus_first_test.conf
dbus_first_test.log: run_murphyd.log
NEEDED_LOGS += dbus_first_test.conf
endif # DBUS_ENABLED

# Actual tests requiring Murphy end

TESTS += stop_murphyd.sh
stop_murphyd.log: $(NEEDED_LOGS)

endif # FMBT_AVAILABLE

TEST_EXTENSIONS = .conf .sh
CONF_LOG_COMPILER = fmbt
