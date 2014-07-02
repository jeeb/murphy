-- define application classes
application_class { name="interrupt", priority=99, modal=true , share=false, order="fifo" }
application_class { name="navigator", priority=4 , modal=false, share=true , order="fifo" }
application_class { name="phone"    , priority=3 , modal=false, share=true , order="lifo" }
application_class { name="game"     , priority=2 , modal=false, share=true , order="lifo" }
application_class { name="player"   , priority=1 , modal=false, share=true , order="lifo" }
application_class { name="implicit" , priority=0 , modal=false, share=true , order="lifo" }

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
         role = { mdb.string, "music", "rw" },
         pid = { mdb.string, "<unknown>", "rw" },
         policy = { mdb.string, "relaxed", "rw" },
         uint   = { mdb.unsigned, 12, "rw" },
         int    = { mdb.integer, -1337, "rw" },
         floaty = { mdb.floating, 23.35, "rw" }
     }
}

resource.class {
     name = "audio_recording",
     shareable = false,
     attributes = {
         role = { mdb.string, "music", "rw" },
         pid = { mdb.string, "<unknown>", "rw" },
         policy = { mdb.string, "relaxed", "rw" }
     }
}

resource.class {
     name = "video_playback",
     shareable = false,
}

resource.class {
     name = "video_recording",
     shareable = false
}
