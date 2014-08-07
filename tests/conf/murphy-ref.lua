m = murphy.get()

-- try loading console plugin
m:try_load_plugin('console')

-- load the dbus plugin if it exists
if m:plugin_exists('dbus') then
    m:load_plugin('dbus')
end

-- load glib plugin, ignoring any errors
m:try_load_plugin('glib')

-- load the native resource plugin
if m:plugin_exists('resource-native') then
    m:load_plugin('resource-native')
    m:info("native resource plugin loaded")
else
    m:info("No native resource plugin found...")
end

if m:plugin_exists('murphydb') then
    m:load_plugin('murpydb')
end

-- load the dbus resource plugin
if m:plugin_exists('resource-dbus') then
    m:try_load_plugin('resource-dbus', {
        dbus_bus = "session",
        dbus_service = "org.Murphy",
        dbus_track = true,
        default_zone = "driver",
        default_class = "implicit"
      })
    m:info("dbus resource plugin loaded")
else
    m:info("No dbus resource plugin found...")
end

-- load the WRT resource plugin
if m:plugin_exists('resource-wrt') then
    m:try_load_plugin('resource-wrt', {
                          address = "wsck:127.0.0.1:4000/murphy",
                          httpdir = "../src/plugins/resource-wrt",
--                          sslcert = 'src/plugins/resource-wrt/resource.crt',
--                          sslpkey = 'src/plugins/resource-wrt/resource.key'
                      })
else
    m:info("No WRT resource plugin found...")
end

-- load the domain control plugin if it exists
if m:plugin_exists('domain-control') then
    m:load_plugin('domain-control')
else
    m:info("No domain-control plugin found...")
end

-- Load up applications, zones and resources
dofile('conf/define_applications_zones_resources.lua')
