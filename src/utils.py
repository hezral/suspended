# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from datetime import datetime

def run_async(func):
    '''
    https://github.com/learningequality/ka-lite-gtk/blob/341813092ec7a6665cfbfb890aa293602fb0e92f/kalite_gtk/mainwindow.py
    http://code.activestate.com/recipes/576683-simple-threading-decorator/
    run_async(func): 
    function decorator, intended to make "func" run in a separate thread (asynchronously).
    Returns the created Thread object
    Example:
        @run_async
        def task1():
            do_something
        @run_async
        def task2():
            do_something_too
    '''
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        # Never return anything, idle_add will think it should re-run the
        # function because it's a non-False value.
        return None

    return async_func

def resume_app(pid):
    from subprocess import Popen, PIPE
    try:
        Popen(['flatpak-spawn', '--host', 'kill', '-CONT', pid])
    except:
        import traceback
        print(traceback.format_exc())

def suspend_app(pid):
    from subprocess import Popen, PIPE
    try:
        Popen(['flatpak-spawn', '--host', 'kill', '-CONT', pid])
    except:
        import traceback
        print(traceback.format_exc())
    ...

def recursive_kill(ppid, pids=None, signal=None):
    from subprocess import Popen, PIPE

    if isinstance(ppid,int):
        ppid = str(ppid)

    if pids is None:
        pids = []
        pids.append(ppid)
        
    try:
        command = "pgrep -P {0}".format(ppid)

        # run_executable = Popen(["flatpak-spawn", "--host", command], stdout=PIPE)
        
        run_executable = Popen(["flatpak-spawn", "--host", "pgrep", "-P", ppid], stdout=PIPE)
        # run_executable = Popen(["pgrep", "-P", ppid], stdout=PIPE)
        stdout, stderr = run_executable.communicate()
        child_pid = stdout.decode("utf-8").split()

        if len(child_pid) != 0:
            pids.append(child_pid[0])
            return recursive_kill(child_pid[0], pids, signal)
        else:
            pids.reverse()
            for pid in pids:
                run_executable = Popen(["flatpak-spawn", "--host", "kill", signal, pid], stdout=PIPE)
                stdout, stderr = run_executable.communicate()
                print(stdout)
            print(pids)
    except:
        import traceback
        print(traceback.format_exc())

def get_flatpak_pid(app_id):
    from subprocess import Popen, PIPE
    try:
        run_executable = Popen(["flatpak-spawn", "--host", "flatpak", "ps", "--columns=pid,application"], stdout=PIPE)
        stdout, stderr = run_executable.communicate()
        for item in stdout.decode("utf-8").split("\n"): # output is delimited by \n or newline
            if item.find(app_id) != -1:
                pid = item.split("\t")[0].rstrip() # each line output is delimited by \t or tab
                return pid
    except:
        import traceback
        print(traceback.format_exc())

def check_stat_file(pid):
    from subprocess import Popen, PIPE, STDOUT
    try:
        cmd = "flatpak-spawn --host ls -qA /proc | grep -c {0}".format(str(pid))
        ps = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        output = ps.communicate()[0]
        return output
    except:
        import traceback
        print(traceback.format_exc())

def read_stat_file(pid):
    from subprocess import Popen, PIPE
    try:
        path = "/proc/{0}/stat".format(pid)
        run_executable = Popen(["flatpak-spawn", "--host", "cat", path], stdout=PIPE)
        stdout, stderr = run_executable.communicate()
        return stdout
    except:
        import traceback
        print(traceback.format_exc())

def parse_proc_state(stat_contents):
    import re
    stat = stat_contents.decode("utf-8")
    cmd = re.findall(r'\(.*?\)', stat)[0]
    stat = stat.replace(cmd, "")
    proc_state = stat.split(" ")[2]
    return proc_state

def get_all_apps(app=None):
    ''' Function to get all apps installed on system using desktop files in standard locations for flatpak, snap, native '''
    import gi, os, re
    from gi.repository import Gio, GLib

    all_apps = {}
    app_name = None
    app_icon = None
    startup_wm_class = None
    no_display = None
    app_exec = None
    duplicate_app = 0

    flatpak_system_app_dirs = "/run/host/usr/share/applications"
    native_system_app_dirs = "/usr/share/applications"
    native_system_app_alt_dirs = "/usr/local/share/applications"
    native_system_flatpak_app_dirs = "/var/lib/flatpak/exports/share/applications"
    native_snap_app_dirs = "/var/lib/snapd/desktop"
    native_user_flatpak_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/flatpak/exports/share/applications")
    native_user_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/applications")
    desktop_file_dirs = [native_system_app_dirs, native_system_app_alt_dirs, flatpak_system_app_dirs, native_system_flatpak_app_dirs, native_snap_app_dirs, native_user_flatpak_app_dirs, native_user_app_dirs]

    # system_app_dirs = "/run/host/usr/share/applications"
    # # system_app_alt_dirs = "/usr/local/share/applications"
    # snap_app_dirs = "/var/lib/snapd/desktop"
    # system_flatpak_app_dirs = "/var/lib/flatpak/exports/share/applications"
    # user_flatpak_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/flatpak/exports/share/applications")
    # user_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/applications")
    # desktop_file_dirs = [system_app_dirs, system_flatpak_app_dirs, snap_app_dirs, user_app_dirs, user_flatpak_app_dirs]

    for dir in desktop_file_dirs:
        if os.path.exists(dir):
            d = Gio.file_new_for_path(dir)
            files = d.enumerate_children("standard::*", 0)
            for desktop_file in files:
                if ".desktop" in desktop_file.get_name():
                    desktop_file_path = ""
                    
                    # print(desktop_file.get_content_type(), os.path.join(dir, desktop_file.get_name()))

                    if "application/x-desktop" in desktop_file.get_content_type():
                        desktop_file_path = os.path.join(dir, desktop_file.get_name())

                    if "inode/symlink" in desktop_file.get_content_type():
                        if ".local/share/flatpak/exports/share/applications" in dir:
                            desktop_file_path = os.path.join(GLib.get_home_dir(), ".local/share/flatpak", os.path.realpath(desktop_file.get_symlink_target()).replace("/home/", ""))

                    if desktop_file_path != "":
                        try:
                            with open(desktop_file_path) as file:
                                lines = file.readlines()
                            contents = ''.join(lines)

                            app_name = re.search("Name=(?P<name>.+)*", contents)
                            app_icon = re.search("Icon=(?P<name>.+)*", contents)
                            startup_wm_class = re.search("StartupWMClass=(?P<name>.+)*", contents)
                            no_display = re.search("NoDisplay=(?P<name>.+)*", contents)
                            app_exec = re.search("Exec=(?P<name>.+)*", contents)
                            flatpak = re.search("X-Flatpak=(?P<name>.+)*", contents)

                            if app_name != None:
                                app_name = app_name.group(1)
                            else:
                                app_name = "unknown"
                            
                            if app_icon != None:
                                app_icon = app_icon.group(1)
                            else:
                                app_icon = "application-default-icon"

                            if startup_wm_class != None:
                                startup_wm_class = startup_wm_class.group(1)

                            if no_display != None:
                                no_display = no_display.group(1)
                                if 'true' in no_display:
                                    no_display = True
                                else:
                                    no_display = False

                            if app_exec != None:
                                app_exec = app_exec.group(1)

                            if flatpak != None:
                                flatpak = True
                            else:
                                flatpak = False

                            if app_name != None and app_icon != None:
                                if no_display is None or no_display is False:
                                    if app_name in all_apps:
                                        duplicate_app += 1
                                        app_name = app_name + "#{0}".format(str(duplicate_app))
                                        all_apps[app_name] = [app_icon, startup_wm_class, no_display, desktop_file_path, app_exec, flatpak]
                                    else:
                                        all_apps[app_name] = [app_icon, startup_wm_class, no_display, desktop_file_path, app_exec, flatpak]
                        except:
                            print(datetime.now(), "Unable to read {0} application info".format(desktop_file_path))

    if app != None:
        return all_apps[app]
    else:
        return all_apps

def get_running_apps():
    running_apps = {}
    all_apps = get_all_apps()

    import os
    import re
    import chardet
    import Xlib
    import Xlib.display

    display = Xlib.display.Display()
    root = display.screen().root

    NET_CLIENT_LIST = display.intern_atom('_NET_CLIENT_LIST')
    NET_DESKTOP_NAMES = display.intern_atom('_NET_DESKTOP_NAMES')
    NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
    GTK_APPLICATION_ID = display.intern_atom('_GTK_APPLICATION_ID')
    WM_NAME = display.intern_atom('WM_NAME')
    WM_CLASS = display.intern_atom('WM_CLASS')
    BAMF_DESKTOP_FILE = display.intern_atom('_BAMF_DESKTOP_FILE')
    NET_WM_PID = display.intern_atom('_NET_WM_PID')
    NET_WM_DESKTOP = display.intern_atom('_NET_WM_DESKTOP')
    
    proc_state = None

    try:
        window_id_list = root.get_full_property(NET_CLIENT_LIST, Xlib.X.AnyPropertyType).value

        for window_id in window_id_list:
            
            window = None
            bamf_desktop_file = None
            gtk_application_id = None
            wm_class = None
            wm_name = None
            pid = None
            proc_state = None
            workspace_n = None

            window = display.create_resource_object('window', window_id)

            if window.get_full_property(BAMF_DESKTOP_FILE, 0):
                encoding = chardet.detect(window.get_full_property(BAMF_DESKTOP_FILE, 0).value)['encoding']
                bamf_desktop_file = window.get_full_property(BAMF_DESKTOP_FILE, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(GTK_APPLICATION_ID, 0):
                encoding = chardet.detect(window.get_full_property(GTK_APPLICATION_ID, 0).value)['encoding']
                gtk_application_id = window.get_full_property(GTK_APPLICATION_ID, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(WM_CLASS, 0):
                encoding = chardet.detect(window.get_full_property(WM_CLASS, 0).value)['encoding']
                wm_class = window.get_full_property(WM_CLASS, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(WM_NAME, 0):
                encoding = chardet.detect(window.get_full_property(WM_NAME, 0).value)['encoding']
                try:
                    wm_name = window.get_full_property(WM_NAME, 0).value.decode(encoding).lower()
                except:
                    wm_name = window.get_full_property(WM_NAME, 0).value.decode("utf-8").lower()

            if window.get_full_property(NET_WM_PID, 0):
                pid = window.get_full_property(NET_WM_PID, 0).value[0]

            if window.get_full_property(NET_WM_DESKTOP, 0):
                workspace_n = window.get_full_property(NET_WM_DESKTOP, 0)
                if workspace_n is not None:
                    workspace_n = workspace_n.value[0]

            for key in sorted(all_apps.keys()):

                app_name = None
                app_name_ori = None
                app_icon = None
                app_icon_ori = None
                startup_wm_class = None
                startup_wm_class_ori = None
                no_display = None
                desktop_file_path = None
                desktop_file_path_ori = None
                app_exec = None
                flatpak = None

                app_name = key.split("#")[0].lower()
                app_name_ori = key.split("#")[0]
                app_icon = all_apps[key][0].lower()
                app_icon_ori = all_apps[key][0]

                if all_apps[key][1] is not None:
                    startup_wm_class = all_apps[key][1].lower()
                    startup_wm_class_ori = all_apps[key][1]
                else:
                    startup_wm_class = None

                no_display = all_apps[key][2]
                    
                desktop_file_path = all_apps[key][3].lower()
                desktop_file_path_ori = all_apps[key][3]

                app_exec = all_apps[key][4]
                flatpak = all_apps[key][5]

                if bamf_desktop_file:
                    if os.path.basename(bamf_desktop_file) == os.path.basename(desktop_file_path):
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break
                        
                elif gtk_application_id:
                    if gtk_application_id == app_icon:
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break

                elif wm_name:
                    if " - " in wm_name:
                        wm_name = wm_name.split(" - ")[-1]
                    if wm_name == app_name or wm_name == startup_wm_class or wm_name in app_icon:
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break

                elif wm_class:
                    wm_class_keys = wm_class.split(",")
                    for wm_class_key in wm_class_keys:
                        if wm_class_key != '':
                            if wm_class_key.lower() in app_icon or wm_class_key.lower() in app_exec:
                                running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                                break
                            elif "-" in wm_class_key:
                                for wm_class_subkey in wm_class_key.split("-"):
                                    if wm_class_subkey.lower() == app_name or wm_class_subkey.lower() == startup_wm_class or wm_class_subkey.lower() in app_icon:
                                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                                        break
        
        display = None
        root = None
        return running_apps

    except Xlib.error.XError: #simplify dealing with BadWindow
        print("badwindow")
        display = None
        root = None
        return None

def get_active_app_using_active_window():
    running_apps = {}
    all_apps = get_all_apps()

    import os
    import re
    import chardet
    import Xlib
    import Xlib.display

    display = Xlib.display.Display()
    root = display.screen().root

    NET_CLIENT_LIST = display.intern_atom('_NET_CLIENT_LIST')
    NET_DESKTOP_NAMES = display.intern_atom('_NET_DESKTOP_NAMES')
    NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
    GTK_APPLICATION_ID = display.intern_atom('_GTK_APPLICATION_ID')
    WM_NAME = display.intern_atom('WM_NAME')
    WM_CLASS = display.intern_atom('WM_CLASS')
    BAMF_DESKTOP_FILE = display.intern_atom('_BAMF_DESKTOP_FILE')
    NET_WM_PID = display.intern_atom('_NET_WM_PID')
    NET_WM_DESKTOP = display.intern_atom('_NET_WM_DESKTOP')
    
    proc_state = None

    try:
        window_id_list = root.get_full_property(NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value

        for window_id in window_id_list:
            
            window = None
            bamf_desktop_file = None
            gtk_application_id = None
            wm_class = None
            wm_name = None
            pid = None
            proc_state = None
            workspace_n = None

            window = display.create_resource_object('window', window_id)

            if window.get_full_property(BAMF_DESKTOP_FILE, 0):
                encoding = chardet.detect(window.get_full_property(BAMF_DESKTOP_FILE, 0).value)['encoding']
                bamf_desktop_file = window.get_full_property(BAMF_DESKTOP_FILE, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(GTK_APPLICATION_ID, 0):
                encoding = chardet.detect(window.get_full_property(GTK_APPLICATION_ID, 0).value)['encoding']
                gtk_application_id = window.get_full_property(GTK_APPLICATION_ID, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(WM_CLASS, 0):
                encoding = chardet.detect(window.get_full_property(WM_CLASS, 0).value)['encoding']
                wm_class = window.get_full_property(WM_CLASS, 0).value.replace(b'\x00',b' ').decode(encoding).lower()
            
            if window.get_full_property(WM_NAME, 0):
                encoding = chardet.detect(window.get_full_property(WM_NAME, 0).value)['encoding']
                try:
                    wm_name = window.get_full_property(WM_NAME, 0).value.decode(encoding).lower()
                except:
                    wm_name = window.get_full_property(WM_NAME, 0).value.decode("utf-8").lower()

            if window.get_full_property(NET_WM_PID, 0):
                pid = window.get_full_property(NET_WM_PID, 0).value[0]

            if window.get_full_property(NET_WM_DESKTOP, 0):
                workspace_n = window.get_full_property(NET_WM_DESKTOP, 0)
                if workspace_n is not None:
                    workspace_n = workspace_n.value[0]

            for key in sorted(all_apps.keys()):

                app_name = None
                app_name_ori = None
                app_icon = None
                app_icon_ori = None
                startup_wm_class = None
                startup_wm_class_ori = None
                no_display = None
                desktop_file_path = None
                desktop_file_path_ori = None
                app_exec = None
                flatpak = None

                app_name = key.split("#")[0].lower()
                app_name_ori = key.split("#")[0]
                app_icon = all_apps[key][0].lower()
                app_icon_ori = all_apps[key][0]

                if all_apps[key][1] is not None:
                    startup_wm_class = all_apps[key][1].lower()
                    startup_wm_class_ori = all_apps[key][1]
                else:
                    startup_wm_class = None

                no_display = all_apps[key][2]
                    
                desktop_file_path = all_apps[key][3].lower()
                desktop_file_path_ori = all_apps[key][3]

                app_exec = all_apps[key][4]
                flatpak = all_apps[key][5]

                if bamf_desktop_file:
                    if os.path.basename(bamf_desktop_file) == os.path.basename(desktop_file_path):
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break
                        
                elif gtk_application_id:
                    if gtk_application_id == app_icon:
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break

                elif wm_name:
                    if " - " in wm_name:
                        wm_name = wm_name.split(" - ")[-1]
                    if wm_name == app_name or wm_name == startup_wm_class or wm_name in app_icon:
                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                        break

                elif wm_class:
                    wm_class_keys = wm_class.split(",")
                    for wm_class_key in wm_class_keys:
                        if wm_class_key != '':
                            if wm_class_key.lower() in app_icon or wm_class_key.lower() in app_exec:
                                running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                                break
                            elif "-" in wm_class_key:
                                for wm_class_subkey in wm_class_key.split("-"):
                                    if wm_class_subkey.lower() == app_name or wm_class_subkey.lower() == startup_wm_class or wm_class_subkey.lower() in app_icon:
                                        running_apps[app_name_ori] = [app_icon_ori, startup_wm_class_ori, no_display, desktop_file_path_ori, app_exec, flatpak, wm_class, wm_name, workspace_n, window_id, pid, proc_state]
                                        break
        display = None
        root = None
        return running_apps

    except Xlib.error.XError: #simplify dealing with BadWindow
        display = None
        root = None
        return None

def get_gdk_window(window_id):
    from gi.repository import Gdk
    from gi.repository import GdkX11

    Gdk.Window.process_all_updates()
    xlib_window = window_id
    gdk_display = GdkX11.X11Display.get_default()
    gdk_window = GdkX11.X11Window.foreign_new_for_display(gdk_display, xlib_window)
    return gdk_window

def desaturate_image(gtk_image):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk

    result = gtk_image.get_pixbuf().copy()
    gtk_image.get_pixbuf().saturate_and_pixelate(result, 0.0, False)
    return Gtk.Image().new_from_pixbuf(result)