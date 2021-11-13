# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import Xlib
from Xlib import X
from Xlib.display import Display
from Xlib.error import XError
from Xlib.xobject.drawable import Window
from Xlib.protocol.rq import Event

import threading

from datetime import datetime


class SuspenderManager():

    stop_thread = False
    id_thread = None
    callback = None

    def __init__(self, gtk_application=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = gtk_application

        # Connect to the X server and get the root window
        self.disp = Display()
        self.root = self.disp.screen().root

        # Prepare the property names we use so they can be fed into X11 APIs
        self.NET_CLIENT_LIST = self.disp.intern_atom('_NET_CLIENT_LIST')
        self.NET_ACTIVE_WINDOW = self.disp.intern_atom('_NET_ACTIVE_WINDOW')
        self.NET_WM_NAME = self.disp.intern_atom('_NET_WM_NAME')  # UTF-8
        self.WM_NAME = self.disp.intern_atom('WM_NAME')           # Legacy encoding
        self.WM_CLASS = self.disp.intern_atom('WM_CLASS')

    def _run(self, callback):

        self.callback = callback

        def init_manager():
            # Listen for _NET_ACTIVE_WINDOW changes
            self.root.change_attributes(event_mask=X.PropertyChangeMask)

            # initialize running apps list
            # self.get_window_name(self.get_active_window()[0])
            # self.handle_change(self.last_seen)


            while True:  # next_event() sleeps until we get an event
                self.handle_xevent(self.disp.next_event())
                if self.stop_thread:
                    break

        self.thread = threading.Thread(target=init_manager)
        self.thread.daemon = True
        self.thread.start()
        print(datetime.now(), "suspender_manager started")

    def _stop(self):
        print(datetime.now(), "suspender_manager stopped")
        self.stop_thread = True

    
    def handle_xevent(self, event: Event):
        """Handler for X events which ignores anything but focus/title change"""
        changed = False

        if event.type != X.PropertyNotify:
            return

        if event.atom == self.NET_ACTIVE_WINDOW:
            # if self.get_active_window()[1]:
                # self.get_window_name(self.last_seen['xid'])  # Rely on the side-effects
            changed = True
        # elif event.atom in (self.NET_WM_NAME, self.WM_NAME):
            # changed = changed or self.get_window_name(self.last_seen['xid'])[1]

        if changed:
            self.handle_change(changed)

    def handle_change(self, changed):
        """Replace this with whatever you want to actually do"""
        # self.callback(new_state['title'])
        print(self.root.get_full_property(self.NET_CLIENT_LIST, Xlib.X.AnyPropertyType).value)
        print(datetime.now(), "new app running", changed)


# import gi
# gi.require_version('Gtk', '3.0')
# gi.require_version('Granite', '1.0')
# gi.require_version('Gst', '1.0')
# from gi.repository import Gtk, Gio, Granite, Gdk, GLib
# sm = SuspenderManager()
# sm._run(callback=None)
# Gtk.main()