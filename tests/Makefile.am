if FMBT_AVAILABLE

TESTS = run_murphyd.sh
NEEDED_LOGS = run_murphyd.log

# Actual tests requiring Murphy begin

if BUILD_RESOURCES
TESTS += test_mrp_resource_native.conf
test_mrp_resource_native.log: run_murphyd.log
NEEDED_LOGS += test_mrp_resource_native.log
endif

if LIBDBUS_ENABLED
TESTS += test_mrp_dbus.conf
test_mrp_dbus.log: run_murphyd.log
NEEDED_LOGS += test_mrp_dbus.log
endif

if SDBUS_ENABLED
TESTS += test_mrp_dbus.conf
test_mrp_dbus.log: run_murphyd.log
NEEDED_LOGS += test_mrp_dbus.log
endif

# Actual tests requiring Murphy end

TESTS += stop_murphyd.sh
stop_murphyd.log: $(NEEDED_LOGS)

TEST_EXTENSIONS = .conf .sh
CONF_LOG_COMPILER = fmbt

endif # FMBT_AVAILABLE
