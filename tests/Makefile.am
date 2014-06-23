TESTS =

if BUILD_RESOURCES
TESTS += test_mrp_resource_native.conf
endif

if LIBDBUS_ENABLED
TESTS += test_mrp_dbus.conf
endif

if SDBUS_ENABLED
TESTS += test_mrp_dbus.conf
endif

TEST_EXTENSIONS = .conf
CONF_LOG_COMPILER = fmbt
