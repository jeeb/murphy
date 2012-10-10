#include <stdlib.h>
#include <murphy/common/debug.h>

/* common/dbus.c */
static mrp_debug_info_t info_0[] = {
    { .line = 133, .func = "purge_filters" },
    { .line = 153, .func = "dbus_disconnect" },
    { .line = 182, .func = "mrp_dbus_connect" },
    { .line = 295, .func = "mrp_dbus_ref" },
    { .line = 301, .func = "mrp_dbus_unref" },
    { .line = 313, .func = "mrp_dbus_acquire_name" },
    { .line = 334, .func = "mrp_dbus_release_name" },
    { .line = 345, .func = "mrp_dbus_get_unique_name" },
    { .line = 350, .func = "name_owner_query_cb" },
    { .line = 372, .func = "name_owner_change_cb" },
    { .line = 417, .func = "mrp_dbus_follow_name" },
    { .line = 452, .func = "mrp_dbus_forget_name" },
    { .line = 486, .func = "purge_name_trackers" },
    { .line = 504, .func = "handler_alloc" },
    { .line = 531, .func = "handler_free" },
    { .line = 544, .func = "handler_list_alloc" },
    { .line = 561, .func = "handler_list_free" },
    { .line = 577, .func = "handler_list_free_cb" },
    { .line = 585, .func = "handler_specificity" },
    { .line = 600, .func = "handler_list_insert" },
    { .line = 621, .func = "handler_list_lookup" },
    { .line = 643, .func = "handler_list_find" },
    { .line = 663, .func = "mrp_dbus_export_method" },
    { .line = 687, .func = "mrp_dbus_remove_method" },
    { .line = 710, .func = "mrp_dbus_add_signal_handler" },
    { .line = 743, .func = "mrp_dbus_del_signal_handler" },
    { .line = 773, .func = "mrp_dbus_subscribe_signal" },
    { .line = 800, .func = "mrp_dbus_unsubscribe_signal" },
    { .line = 819, .func = "mrp_dbus_install_filterv" },
    { .line = 873, .func = "mrp_dbus_install_filter" },
    { .line = 889, .func = "mrp_dbus_remove_filterv" },
    { .line = 921, .func = "mrp_dbus_remove_filter" },
    { .line = 937, .func = "dispatch_method" },
    { .line = 978, .func = "dispatch_signal" },
    { .line = 1032, .func = "call_reply_cb" },
    { .line = 1051, .func = "mrp_dbus_call" },
    { .line = 1133, .func = "mrp_dbus_send" },
    { .line = 1214, .func = "mrp_dbus_send_msg" },
    { .line = 1220, .func = "mrp_dbus_call_cancel" },
    { .line = 1244, .func = "mrp_dbus_reply" },
    { .line = 1281, .func = "call_free" },
    { .line = 1288, .func = "purge_calls" },
    { .line = 1306, .func = "mrp_dbus_signal" },
    { .line = 0, .func = NULL }
};
static mrp_debug_file_t file_0 = {
    .file = "common/dbus.c",
    .info = info_0
};

/* common/dbus-glue.c */
static mrp_debug_info_t info_1[] = {
    { .line = 67, .func = "dispatch_watch" },
    { .line = 93, .func = "watch_freed_cb" },
    { .line = 105, .func = "add_watch" },
    { .line = 154, .func = "del_watch" },
    { .line = 169, .func = "toggle_watch" },
    { .line = 180, .func = "dispatch_timeout" },
    { .line = 194, .func = "timeout_freed_cb" },
    { .line = 207, .func = "add_timeout" },
    { .line = 238, .func = "del_timeout" },
    { .line = 253, .func = "toggle_timeout" },
    { .line = 264, .func = "wakeup_mainloop" },
    { .line = 274, .func = "glue_free_cb" },
    { .line = 303, .func = "pump_cb" },
    { .line = 316, .func = "dispatch_status_cb" },
    { .line = 339, .func = "mrp_dbus_setup_connection" },
    { .line = 0, .func = NULL }
};
static mrp_debug_file_t file_1 = {
    .file = "common/dbus-glue.c",
    .info = info_1
};

/* common/dbus-transport.c */
static mrp_debug_info_t info_2[] = {
    { .line = 87, .func = "parse_address" },
    { .line = 193, .func = "copy_address" },
    { .line = 246, .func = "check_address" },
    { .line = 254, .func = "peer_address" },
    { .line = 296, .func = "dbus_resolve" },
    { .line = 312, .func = "dbus_open" },
    { .line = 320, .func = "dbus_createfrom" },
    { .line = 334, .func = "dbus_bind" },
    { .line = 410, .func = "dbus_autobind" },
    { .line = 428, .func = "dbus_close" },
    { .line = 462, .func = "dbus_msg_cb" },
    { .line = 505, .func = "dbus_data_cb" },
    { .line = 548, .func = "dbus_raw_cb" },
    { .line = 591, .func = "peer_state_cb" },
    { .line = 625, .func = "dbus_connect" },
    { .line = 662, .func = "dbus_disconnect" },
    { .line = 676, .func = "dbus_sendmsgto" },
    { .line = 714, .func = "dbus_sendmsg" },
    { .line = 724, .func = "dbus_sendrawto" },
    { .line = 769, .func = "dbus_sendraw" },
    { .line = 779, .func = "dbus_senddatato" },
    { .line = 817, .func = "dbus_senddata" },
    { .line = 827, .func = "get_array_signature" },
    { .line = 852, .func = "msg_encode" },
    { .line = 1019, .func = "msg_decode" },
    { .line = 1228, .func = "data_encode" },
    { .line = 1401, .func = "member_type" },
    { .line = 1415, .func = "data_decode" },
    { .line = 1620, .func = "raw_encode" },
    { .line = 1659, .func = "raw_decode" },
    { .line = 0, .func = NULL }
};
static mrp_debug_file_t file_2 = {
    .file = "common/dbus-transport.c",
    .info = info_2
};

/* table of all files */
static mrp_debug_file_t *debug_files[] = {
    &file_0,
    &file_1,
    &file_2,
    NULL
};

#include <murphy/common/debug-auto-register.c>
