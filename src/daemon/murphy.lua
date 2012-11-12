m = murphy.get()

-- try loading console plugin
m:try_load_plugin('console')

-- load a test plugin
if m:plugin_exists('test') then
    m:load_plugin('test', {
                       string2  = 'this is now string2',
                       boolean2 = true,
                       int32 = -981,
                       double = 2.73 })
--    m:load_plugin('test', 'test2')
--    m:info("Successfully loaded two instances of test...")
end

-- load the dbus plugin if it exists
if m:plugin_exists('dbus') then
    m:load_plugin('dbus')
end

-- load glib plugin, ignoring any errors
m:try_load_plugin('glib')

-- try loading the signalling plugin
m:try_load_plugin('signalling', { address = 'internal:signalling' })

-- load the native resource plugin
if m:plugin_exists('resource-native') then
    m:load_plugin('resource-native')
    m:info("native resource plugin loaded")
else
    m:info("No native resource plugin found...")
end

-- load the domain control plugin if it exists
if m:plugin_exists('domain-control') then
    m:load_plugin('domain-control')
else
    m:info("No domain-control plugin found...")
end


-- define application classes
application_class { name = "navigator", priority = 4 }
application_class { name = "phone"    , priority = 3 }
application_class { name = "game"     , priority = 2 }
application_class { name = "player"   , priority = 1 }
application_class { name = "implicit" , priority = 0 }

-- define zone attributes
zone.attributes {
    type = {mdb.string, "common", "rw"},
    location = {mdb.string, "anywhere", "rw"}
}

-- define zones
zone {
     name = "driver",
     attributes = {
         type = "common",
         location = "front-left"
     }
}

zone {
     name = "passanger1",
     attributes = {
         type = "private",
         location = "front-right"
     }
}

zone {
     name = "passanger2",
     attributes = {
         type = "private",
         location = "back-left"
     }
}

zone {
     name = "passanger3",
     attributes = {
         type = "private",
         location = "back-right"
     }
}

zone {
     name = "passanger4",
     attributes = {
         type = "private",
         location = "back-left"
     }
}


-- define resource classes
resource.class {
     name = "audio_playback",
     shareable = true,
     attributes = {
         role = { mdb.string, "music", "rw" }
     }
}

resource.class {
     name = "audio_recording",
     shareable = true
}

resource.class {
     name = "video_playback",
     shareable = false,
}

resource.class {
     name = "video_recording",
     shareable = false
}

-- test for creating selections
mdb.select {
           name = "audio_owner",
           table = "audio_playback_owner",
           columns = {"application_class"},
           condition = "zone_name = 'driver'",
}