TESTS = run_murphyd.sh

if BUILD_RESOURCES
TESTS += test_mrp_resource_native.conf
test_mrp_resource_native.log: run_murphyd.log
endif

if LIBDBUS_ENABLED
TESTS += test_mrp_dbus.conf
test_mrp_dbus.log: run_murphyd.log
endif

if SDBUS_ENABLED
TESTS += test_mrp_dbus.conf
test_mrp_dbus.log: run_murphyd.log
endif

TESTS += stop_murphyd.sh
stop_murphyd.log: run_murphyd.log test_mrp_resource_native.log test_mrp_dbus.log

TEST_EXTENSIONS = .conf .sh
CONF_LOG_COMPILER = fmbt
