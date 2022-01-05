# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from datetime import datetime

import gi
gi.require_version('Gtk', '3.0')
gi.require_version("Wnck", "3.0")
from gi.repository import GLib, Gtk, Wnck

import time
import threading

from .app_obj import AppObject

class AppManager():
    
    screen = Wnck.Screen.get_default()
    last_running_apps = {}
    current_running_apps = {}

    stop_thread = False

    def __init__(self, gtk_application=None, polling_interval=30, *args, **kwargs):

        self.app = gtk_application
        self.polling_interval = polling_interval

        self.initialize_running_apps()
        self._run()
        GLib.timeout_add(5000, self.initialize_event_handling, None) #delay to avoid clash with poll_status

    def initialize_event_handling(self, *args):
        self.screen.connect("application-opened", self.on_application_closed)
        self.screen.connect("application-closed", self.on_application_opened)
        self.screen.connect("active-window-changed", self.on_active_window_changed)
        print(datetime.now(), "app_manager: event handling started")

    def initialize_running_apps(self):
        running_apps = self.app.utils.get_running_apps()

        for key in self.app.gio_settings.get_value("excluded-apps").get_strv():
            if key in running_apps.keys():
                running_apps.pop(key)

        for key in sorted(running_apps.keys(), reverse=True):
            app = running_apps[key]
            self.last_running_apps[key] = AppObject(
                                                name=key,
                                                icon=app[0],
                                                startup_wm_class=app[1],
                                                no_display=app[2],
                                                desktop_file=app[3],
                                                app_exec=app[4],
                                                flatpak=app[5],
                                                wm_class=app[6],
                                                wm_name=app[7],
                                                workspace_n=app[8],
                                                window_id=app[9],
                                                pid=app[10],
                                            )
            self.app.window.update_app_list(self.last_running_apps[key])

    def _run(self):

        def init_manager():
            while True:  
                GLib.idle_add(self.poll_status, ("main-loop"))
                # self.poll_status(event="main-loop")
                if self.stop_thread:
                    break
                time.sleep(self.polling_interval)

        self.thread = threading.Thread(target=init_manager)
        self.thread.daemon = True
        self.thread.start()

        print(datetime.now(), "app_manager started")

    def _stop(self):
        self.stop_thread = True
        print(datetime.now(), "app_manager stopped")
        self.screen.disconnect_by_func( self.poll_status)
        # self.screen.connect("application-closed", self.poll_status)
        # self.screen.connect("active-window-changed", self.poll_status)
        print(datetime.now(), "app_manager event handling stopped")

    def poll_status(self, event=None, *args):

        self.current_running_apps = self.app.utils.get_running_apps()

        for key in self.app.gio_settings.get_value("excluded-apps").get_strv():
            if key in self.current_running_apps.keys():
                self.current_running_apps.pop(key)

        try:
            for key in sorted(self.current_running_apps.keys(), reverse=True):
                app = self.current_running_apps[key]
                self.current_running_apps[key] = AppObject(
                                                        name=key,
                                                        icon=app[0],
                                                        startup_wm_class=app[1],
                                                        no_display=app[2],
                                                        desktop_file=app[3],
                                                        app_exec=app[4],
                                                        flatpak=app[5],
                                                        wm_class=app[6],
                                                        wm_name=app[7],
                                                        workspace_n=app[8],
                                                        window_id=app[9],
                                                        pid=app[10]
                                                    )

            added, removed, modified, same = self.compare_running_apps(self.current_running_apps, self.last_running_apps)

            if len(added) != 0:
                for x in added:
                    self.last_running_apps[x] = self.current_running_apps[x]
                    self.app.window.update_app_list(self.last_running_apps[x], "add")
            print("added: ", added, len(added))
            
            if len(removed) != 0:
                for x in removed:
                    stat = self.app.utils.check_stat_file(self.last_running_apps[x].pid).decode('utf-8')
                    if int(stat) == 0:
                        self.app.window.update_app_list(self.last_running_apps[x], "remove")
                        self.last_running_apps.pop(x)
            print("removed: ",removed, len(removed))

            if len(modified) != 0:
                for x in modified:
                    self.update_app_obj(self.last_running_apps[x], self.current_running_apps[x])
                    # self.last_running_apps[x] = self.current_running_apps[x]
                    self.app.window.update_app_list(self.last_running_apps[x], "update")
            print("modified: ", len(modified))

            # print("same: ",same, len(same))

        except:
            import traceback
            print(datetime.now(), traceback.format_exc())

        # print("--")
        print(datetime.now(), "app_manager: poll status > running apps event:{0}".format(event))
        # for key in self.last_running_apps.keys():
            # app = self.last_running_apps[key]
            # print("app:{0}, pid:{1}, proc_state:{2}, window_id:{3}".format(app.name, app.pid, app.proc_state, app.proc_state_name))
        # print("--")

    def on_application_closed(self, screen, app):
        self.poll_status(event="application-closed")

    def on_application_opened(self, screen, app):
        self.poll_status(event="application-opened")

    def on_active_window_changed(self, *args):
        self.poll_status(event="active-window-changed")
        active_app = self.app.utils.get_active_app_using_active_window()

        # for key in active_app.keys():
        #     if key != "Suspended":
        #         print(self.last_running_apps[key].resume_on_activate_window)
        #         print(self.last_running_apps[key].suspended)

    def compare_running_apps(self, dict_1, dict_2):
        dict_1_keys = set(dict_1.keys())
        d2_keys = set(dict_2.keys())
        shared_keys = dict_1_keys.intersection(d2_keys)
        added = dict_1_keys - d2_keys
        removed = d2_keys - dict_1_keys
        modified = {o : (dict_1[o], dict_2[o]) for o in shared_keys if dict_1[o] != dict_2[o]}
        same = set(o for o in shared_keys if dict_1[o] == dict_2[o])
        return added, removed, modified, same

    def update_app_obj(self, app_obj1, app_obj2):
        from dataclasses import field, fields

        session_settings = [
                            "proc_state",
                            "proc_state_name",
                            "suspended_timestamp",
                            "suspended",
                            ]

        for field1 in fields(app_obj1.__class__):
            for field2 in fields(app_obj2.__class__):
                if field1.name in session_settings:
                    if field1.name == field2.name:
                        if getattr(app_obj1, field1.name) != getattr(app_obj2, field2.name):
                            setattr(app_obj1, field1.name, getattr(app_obj2, field2.name))

