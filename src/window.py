# window.py
#
# Copyright 2021 adi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import Gtk, Handy, Gdk, Gio, Granite, GLib, GdkPixbuf, Pango, GObject

from .settings_view import SettingsView
from .workspaces_view import WorkspacesView


class SuspendedWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'SuspendedWindow'

    Handy.init()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.modulepath = os.path.dirname(__file__)

        self.workspaces_view = WorkspacesView()
        self.settings_view = SettingsView()
        self.settings_view.connect("notify::visible", self.on_view_visible)
        self.header = self.generate_headerbar(settings_view=self.settings_view)
        
        self.stack = Gtk.Stack()
        self.stack.props.name = "main-stack"
        self.stack.props.transition_type = Gtk.StackTransitionType.CROSSFADE
        self.stack.props.transition_duration = 150
        self.stack.add_named(self.settings_view, self.settings_view.get_name())
        self.stack.add_named(self.workspaces_view, self.workspaces_view.get_name())

        grid = Gtk.Grid()
        grid.props.expand = True
        grid.attach(self.header, 0, 0, 1, 1)
        grid.attach(self.stack, 0, 1, 1, 1)

        self.add(grid)
        self.show_all()
        self.get_style_context().add_class("rounded")
        self.set_size_request(700, 550) #set width to -1 to expand and retract based on content
        

    def generate_headerbar(self, settings_view):
        header_label = Gtk.Label()
        header_label.get_style_context().add_class("header-label")

        #------ view switch ----#
        icon_theme = Gtk.IconTheme.get_default()
        icon_theme.prepend_search_path(os.path.join(self.modulepath, "..", "data/icons"))
        view_switch = Granite.ModeSwitch.from_icon_name("com.github.hezral.quickword-symbolic", "preferences-system-symbolic")
        view_switch.props.valign = Gtk.Align.CENTER
        view_switch.props.name = "viewswitch"
        view_switch.bind_property("active", settings_view, "visible", GObject.BindingFlags.BIDIRECTIONAL)

        #-- header construct--------#
        headerbar = Handy.HeaderBar()
        headerbar.pack_start(header_label)
        headerbar.pack_end(view_switch)
        headerbar.props.show_close_button = True
        headerbar.props.decoration_layout = "close"
        headerbar.get_style_context().add_class("default-decoration")
        headerbar.get_style_context().add_class(Gtk.STYLE_CLASS_FLAT)
        return headerbar

            
    def on_view_visible(self, view, gparam=None, runlookup=None, word=None):
        
        if view.is_visible():
            self.current_view = "settings-view"

        else:
            view.hide()
            self.current_view = "workspaces-view"

        self.stack.set_visible_child_name(self.current_view)

