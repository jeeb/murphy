if FMBT_AVAILABLE

TESTS = run_murphyd.sh
NEEDED_LOGS = run_murphyd.log

# Actual tests requiring Murphy begin

if BUILD_RESOURCES
TESTS += test_mrp_resource_native.conf
test_mrp_resource_native.log: run_murphyd.log
NEEDED_LOGS += test_mrp_resource_native.log

TESTS += test_mrp_resource.conf
test_mrp_resource_native.log: run_murphyd.log
NEEDED_LOGS += test_mrp_resource.log

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
TESTS += test_mrp_websockets.conf
test_mrp_websockets.log: run_murphyd.log
NEEDED_LOGS += test_mrp_websockets.log
endif

if BUILD_RESOURCES
if DBUS_ENABLED
TESTS += run_multiprotocol_comparison.sh
run_multiprotocol_comparison.log: run_murphyd.log
NEEDED_LOGS += run_multiprotocol_comparison.log
endif
endif

# Actual tests requiring Murphy end

TESTS += stop_murphyd.sh
stop_murphyd.log: $(NEEDED_LOGS)

endif # FMBT_AVAILABLE

TEST_EXTENSIONS = .conf .sh
CONF_LOG_COMPILER = fmbt
