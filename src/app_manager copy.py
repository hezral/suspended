# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>


import gi
gi.require_version('Gtk', '3.0')
gi.require_version("Bamf", "3")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, Bamf, Wnck, Gdk, GdkX11
import re
import subprocess

# list of excluded apps by default
exclude_list = ('Wingpanel',
                'Plank',)

#------------------CLASS-SEPARATOR------------------#


class AppManager():
    
    screen = Wnck.Screen.get_default()
    matcher = Bamf.Matcher.get_default()
    gdk_display = GdkX11.X11Display.get_default()


    def __init__(self, gtk_application, *args, **kwargs):

        self.screen.force_update()
        Gdk.Window.process_all_updates()
        
        # create empty dictionary instaces for each workspace available
        # these will hold the apps info nested dictionary
        self.update_workspaces()

        # get all running applications
        self.update_running_apps()

        #self.on_events("startup")
        self.app = gtk_application
        
        # setup signals
        self.screen.connect("application-opened", self.on_screen_event, "app-open")
        self.screen.connect("application-closed", self.on_screen_event, "app-close")
        self.screen.connect("workspace_created", self.on_screen_event, "workspace-create")
        self.screen.connect("workspace_destroyed", self.on_screen_event, "workspace-destroy")

    def update_workspaces(self):

        self.workspaces = {}
        self.workspaces.clear()

        for workspace in self.screen.get_workspaces():
            self.workspaces[workspace.get_number()] = {}

    def update_running_apps(self):
        """ get all running application and populate workspaces dictionary """

        for app in self.matcher.get_running_applications():
            if app.get_name() not in exclude_list and app.get_windows() != 0:
                self.get_application_info(app)

    def update_running_app_windows(self):
        print("run")

    def get_application_info(self, bamf_application):
        """ get application info and add to workspaces dictionary based which workspace the app is in """

        name = bamf_application.get_name()
        # print(bamf_application.get_application_menu())

        for win in bamf_application.get_windows():
            print(name, win.get_pid())

        for xid in bamf_application.get_xids():

            # xid = bamf_application.get_xids()[0]
            xid = xid
            desktop_file = bamf_application.get_desktop_file()

            

            # monitor_number = bamf_application.get_window_for_xid(xid).get_monitor()
            try: 
                gdk_window = GdkX11.X11Window.foreign_new_for_display(self.gdk_display, xid)
            except:
                gdk_window = None
            
            # wnck_window = [window for window in self.screen.get_windows() if xid == window.get_xid()][0]
            # wnck_window.connect("workspace_changed", self.on_window_event, "window-workspace-changed")

            # for window in self.screen.get_windows():
            #     if xid == window.get_xid():
            #         print("window count", window.get_workspace().get_name(), window.get_name())

            for wnck_window in self.screen.get_windows():
                if xid == wnck_window.get_xid():
                    wnck_window.connect("workspace_changed", self.on_screen_event, "window-workspace-changed")

                    window_title = wnck_window.get_name()
                    wnck_wm_class_name = wnck_window.get_class_instance_name()
                    wnck_wm_class_group = wnck_window.get_class_group_name()

                    wnck_app = wnck_window.get_application()
                    wnck_xid = wnck_app.get_xid()

                    app_pid, is_flatpak, app_id = self.find_pid(wnck_window, desktop_file)
                    
                    if app_id is None:
                        app_id = wnck_window.get_class_instance_name()


                    proc_state = self.parse_proc_state(app_pid)

                    icon_pixbuf = wnck_app.get_icon() #gdkpixbuf
                    icon_name = bamf_application.get_icon() #str icon_name

                    if wnck_window.get_workspace() is not None:
                        workspace_n = wnck_window.get_workspace().get_number()
                        workspace_name = wnck_window.get_workspace().get_name()
                    else:
                        workspace_n = None
                        workspace_name = None
                    
                    if workspace_n is not None:
                        app_info = {
                                    "name": name, 
                                    "app_pid": app_pid,
                                    "wnck_xid": wnck_xid, 
                                    "xid": xid, 
                                    "workspace_n": workspace_n, 
                                    "workspace_name": workspace_name, 
                                    "icon": icon_pixbuf, 
                                    "icon_name": icon_name, 
                                    "desktop_file": desktop_file,
                                    "wnck_wm_class_name": wnck_wm_class_name,
                                    "wnck_wm_class_group": wnck_wm_class_group,
                                    "gdk_window": gdk_window,
                                    "proc_state": proc_state,
                                    # "monitor_number": monitor_number
                                    "window_title": window_title,
                                    "is_flatpak": is_flatpak,
                                    "app_id": app_id
                                }

                        # add app info dict to workspace dictionary using wnck_xid as key since its unique for multi window cases
                        self.workspaces[workspace_n][wnck_xid] = app_info

    def find_pid(self, wnck_window, desktop_file):
        """ very hacky way to identify app is flatpak or not """
        try:
            if desktop_file.find("flatpak") != -1:
                is_flatpak = True
                # some flatpak apps don't return a valid wm_class_name, using the desktop filename as workaround
                # split desktop_file since its a full path, get the last slice, split by dot and join the first 3 slice as it follows RDNN naming, hopefully
                app_id = ".".join(desktop_file.split("/")[-1].split(".")[0:3]) 

                run_executable = subprocess.Popen(["flatpak", "ps", "--columns=pid,application"], stdout=subprocess.PIPE)
                stdout, stderr = run_executable.communicate()
                for item in stdout.decode("utf-8").split("\n"): # output is delimited by \n or newline
                    if item.find(app_id) != -1:
                        pid = item.split("\t")[0].rstrip() # each line output is delimited by \t or tab
                        return pid, is_flatpak, app_id
            # elif desktop_file is None:
            #     is_flatpak = True
            #     run_executable = subprocess.Popen(["flatpak", "ps", "--columns=pid,application"], stdout=subprocess.PIPE)
            #     stdout, stderr = run_executable.communicate()
            #     for item in stdout.decode("utf-8").split("\n"): # output is delimited by \n or newline
            #         if item.find(app_id) != -1:
            #             pid = item.split("\t")[0].rstrip() # each line output is delimited by \t or tab
            #             return pid, is_flatpak, app_id

            else:
                pid = wnck_window.get_pid()
                is_flatpak = False
                app_id = None
                return pid, is_flatpak, app_id
        except:
            pid = wnck_window.get_pid()
            is_flatpak = False
            app_id = None
            return pid, is_flatpak, app_id

    def parse_proc_state(self, pid):
        file = open("/proc" + "/" + str(pid) + "/" + "stat", "r")
        stat = file.read()
        cmd = re.findall(r'\(.*?\)', stat)[0]
        stat = stat.replace(cmd, "")
        proc_state = stat.split(" ")[2]
        return proc_state

    def on_screen_event(self, *args):

        second_arg = locals().get('args')[1]
        event_type = locals().get('args')[-1]

        if isinstance(second_arg, Wnck.Application):
            wnck_application = locals().get('args')[1]
            if wnck_application.get_name().capitalize() not in exclude_list:
                self.update_workspaces()
                self.update_running_apps()
        else:
            self.update_workspaces()
            self.update_running_apps()

        # self.on_events(event_type)
        workspaces_view = self.app.window.get_window_child(Gtk.Stack).get_child_by_name("workspaces-view")
        workspaces_view.emit("on-workspace-view-event", self.workspaces)
        self.on_events(event_type)

    def on_events(self, event_type):
        # for debug
        from gi.repository import Gio
        all_apps = Gio.AppInfo.get_all()
        # for app in all_apps:
        #     if app.get_startup_wm_class() is not None:
        #         print(app.get_startup_wm_class())

        print(event_type)
        for workspace_number in self.workspaces:
            for app_xid in self.workspaces[workspace_number]:
                print("Workspace:", workspace_number + 1, 
                        # "Monitor:", self.workspaces[workspace_number][app_xid]["monitor_number"], 
                        "Name:", self.workspaces[workspace_number][app_xid]["name"], 
                        "ID:", self.workspaces[workspace_number][app_xid]["app_id"], 
                        "Desktop File:", self.workspaces[workspace_number][app_xid]["desktop_file"], 
                        "PID:", self.workspaces[workspace_number][app_xid]["app_pid"], 
                        "WM_CLASS_NAME:", self.workspaces[workspace_number][app_xid]["wnck_wm_class_name"], 
                        "WM_CLASS_GROUP:", self.workspaces[workspace_number][app_xid]["wnck_wm_class_group"], 
                        # self.workspaces[workspace_number][app_xid]["proc_state"]
                        )


apps_manager = AppManager(gtk_application=None)

# from conf_manager import ConfigManager
# configs_manager = ConfigManager(gtk_application=None)

import signal
from gi.repository import GLib
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, Gtk.main_quit) 

Gtk.main()


