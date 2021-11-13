# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Handy, GObject, Gdk

from .mode_switch import ModeSwitch

from datetime import datetime

class SuspendedWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'SuspendedWindow'

    Handy.init()

    pull_to_search_count = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = self.props.application

        self.headerbar = self.generate_headerbar()
        self.searchbar = self.generate_searchbar()
        self.app_grid = self.generate_app_grid()

        self.stack = Gtk.Stack()
        self.stack.props.expand = True
        self.stack.add_named(self.app_grid, "app-grid")

        self.grid = Gtk.Grid()
        self.grid.props.expand = True
        self.grid.attach(self.headerbar, 0, 0, 1, 1)
        self.grid.attach(self.searchbar, 0, 1, 1, 1)
        self.grid.attach(self.stack, 0, 2, 1, 1)

        self.add(self.grid)
        default_width = 480
        default_height = 520
        self.props.default_width = default_width
        self.props.default_height = self.app.gio_settings.get_int("window-height")
        geometry = Gdk.Geometry()
        setattr(geometry, 'min_width', default_width)
        setattr(geometry, 'min_height', default_height)
        setattr(geometry, 'max_width', default_width)
        setattr(geometry, 'max_height', 800)
        setattr(geometry, 'base_width', default_width)
        setattr(geometry, 'base_height', default_height)
        self.set_geometry_hints(None, geometry, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE | Gdk.WindowHints.BASE_SIZE)

        self.move(self.app.gio_settings.get_int("pos-x"), self.app.gio_settings.get_int("pos-y"))
        self.set_size_request(default_width, -1)

        self.show_all()
        self.connect("delete-event", self.on_close_window)

    def on_close_window(self, window=None, event=None):
        width, height = self.get_size()
        x, y = self.get_position()

        self.app.gio_settings.set_int("pos-x", x)
        self.app.gio_settings.set_int("pos-y", y)
        self.app.gio_settings.set_int("window-height", height)
        self.app.gio_settings.set_int("window-width", width)

        return False

    def generate_headerbar(self):
        light = Gtk.Image().new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        dark = Gtk.Image().new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        modeswitch = ModeSwitch(None, dark, None, None)
        modeswitch.switch.bind_property("active", self.app.gtk_settings, "gtk_application_prefer_dark_theme", GObject.BindingFlags.INVERT_BOOLEAN)

        header = Handy.HeaderBar()
        header.props.show_close_button = True
        header.props.hexpand = True
        header.props.title = "Suspended"
        # header.props.has_subtitle = True
        # header.props.subtitle = "0 apps"
        header.props.decoration_layout = "close:"
        header.pack_end(modeswitch)

        return header

    def generate_searchbar(self):
        searchentry = Gtk.SearchEntry()
        searchentry.props.placeholder_text = "Search..."
        searchentry.props.margin = 15
        searchentry.props.margin_bottom = 2
        searchentry.props.halign = Gtk.Align.FILL
        searchentry.props.valign = Gtk.Align.FILL
        searchentry.props.hexpand = True
        searchentry.set_size_request(-1, 40)
        searchentry.connect("search-changed", self.on_search_entry_changed)
        searchentry_revealer = Gtk.Revealer()
        searchentry_revealer.add(searchentry)
        return searchentry_revealer

    def generate_app_grid(self):
        self.app_list = Gtk.ListBox()
        self.app_list.set_sort_func(self.sort_listboxbox)
        self.app_list.set_header_func(self.header_func_listbox)
        self.app_list.connect("row_activated", self.on_app_list_item_activated)
        self.app_list.connect("row_selected", self.on_app_list_item_selected)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.props.expand = True
        scrolled_window.props.margin = 15
        scrolled_window.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        scrolled_window.props.shadow_type = Gtk.ShadowType.ETCHED_IN
        scrolled_window.add(self.app_list)
        scrolled_window.set_size_request(-1, 300)
        vadjustment = scrolled_window.props.vadjustment
        # vadjustment.connect("notify::value", self.on_scroll)

        scrolled_window.connect("edge_overshot", self.on_scrolling)
        vadjustment.connect("value-changed", self.on_vadjusment_changed)

        return scrolled_window

    def on_app_list_item_activated(self, listbox, row):
        row.get_child().toggle_app_settings()

    def on_app_list_item_selected(self, listbox, row):
        for child in listbox.get_children():
            if child != row:
                child.get_child().revealer.set_reveal_child(False)

    def on_scroll(self, vadjustment, value):
        if vadjustment.props.value > 0.8 * (vadjustment.props.upper - vadjustment.props.page_size):
            print("show")
        else:
            print("hide")

    def on_scrolling(self, scrolledwindow, button_position):
        if button_position.value_name == "GTK_POS_TOP":
            self.pull_to_search_count += 1
            if self.pull_to_search_count > 1:
                self.searchbar.set_reveal_child(True)

    def on_vadjusment_changed(self, adjustment):
        if adjustment.props.value > 0:
            self.searchbar.set_reveal_child(False)
            self.pull_to_search_count = 0

    def update_app_list(self, app_object=None, action=None):
        if action is None or action == "add":
            self.app_list.insert(AppListItem(app_object), 0)
        
        if action == "remove":
            app_list_item = [child for child in self.app_list.get_children() if child.get_child().app_object.name == app_object.name][0]
            app_list_item.destroy()
        
        if action == "update":
            app_list_item = [child for child in self.app_list.get_children() if child.get_child().app_object.name == app_object.name][0]
            # app_list_item.get_child().show_all()
            # app_list_item.show_all()
            app_list_item.destroy()
            self.app_list.insert(AppListItem(app_object), 0)

            # self.app_list.invalidate_headers()
            # self.app_list.invalidate_sort()

        self.app_list.show_all()

    def sort_listboxbox(self, child1, child2):
        state1 = child1.get_child().app_object.proc_state
        state2 = child2.get_child().app_object.proc_state
        if state1 == "S":
            state1 = 1
        else:
            state1 = 0
        if state2 == "S":
            state2 = 1
        else:
            state2 = 0
        return state1 < state2

    def on_search_entry_changed(self, search_entry):
        if self.stack.get_visible_child_name() == "app-grid":
            self.app_list.invalidate_filter()
            self.filter_listbox(search_entry)

    def filter_listbox(self, search_entry):
        def filter_func(row, search_text):
            app_list_item = row.get_child()
            if search_text in app_list_item.app_object.name.lower():
                return True
            else:
                return False

        search_text = search_entry.get_text()
        search_text = search_text.lower()
        self.app_list.set_filter_func(filter_func, search_text)

    def header_func_listbox(self, row, before, user_data=None):
        def generate_row_header(row):
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.props.expand = True
            label = Gtk.Label(row.get_child().app_object.proc_state_name)
            label.props.halign = Gtk.Align.START
            label.props.margin = 5
            label.props.name = "listboxrow-header"
            grid = Gtk.Grid()
            grid.props.expand = True
            grid.props.name = "listboxrow-header"
            grid.attach(label, 0, 0, 1, 1)
            grid.attach(separator, 0, 1, 1, 1)
            grid.show_all()
            return grid

        if before:
            if row:
                if row.get_header(): 
                    if row.get_child().app_object.proc_state != before.get_child().app_object.proc_state:
                        row.set_header(generate_row_header(row))
                else:
                    if row.get_child().app_object.proc_state != before.get_child().app_object.proc_state:
                        row.set_header(generate_row_header(row))
        else:
            if row:
                row.set_header(generate_row_header(row))


class AppListItem(Gtk.Grid):
    def __init__(self, app_object, **kwargs):

        super().__init__(**kwargs)

        self.app_object = app_object

        self.props.name = "app-list-item"
        self.props.column_spacing = 10
        self.props.expand = True
        self.props.halign = Gtk.Align.FILL

        self.app_icon = Gtk.Image().new_from_icon_name(icon_name=app_object.icon, size=Gtk.IconSize.DIALOG)
        self.app_icon.set_pixel_size(48)

        self.app_name = Gtk.Label(app_object.name)
        self.app_name.props.expand = True
        self.app_name.props.halign = Gtk.Align.START

        self.grid_top = Gtk.Grid()
        self.grid_top.props.name = "app-list-item-top"
        self.grid_top.props.column_spacing = 10
        self.grid_top.props.row_spacing = 4
        self.grid_top.props.hexpand = True
        self.grid_top.props.halign = Gtk.Align.FILL
        self.grid_top.attach(self.app_icon, 0, 0, 1, 1)
        self.grid_top.attach(self.app_name, 1, 0, 1, 1)

        enable_label = Gtk.Label("Enable: ")
        enable_label.props.expand = True
        enable_label.props.halign = Gtk.Align.END
        # enable_label.props.valign = Gtk.Align.START

        self.enable_suspend = Gtk.Switch()
        self.enable_suspend.props.can_focus = False
        self.enable_suspend.props.valign = Gtk.Align.CENTER
        self.enable_suspend.props.halign = Gtk.Align.START
        self.enable_suspend.set_size_request(32, -1)
        self.enable_suspend.get_style_context().add_class("miniswitch")
        self.enable_suspend.connect("notify::active", self.toggle_enable_suspend)
        
        self.suspend_label = Gtk.Label("Suspend: ")
        self.suspend_label.props.expand = True
        self.suspend_label.props.margin_top = 5
        self.suspend_label.props.halign = Gtk.Align.END
        self.suspend_label.props.valign = Gtk.Align.START
        
        self.suspend_on_battery = Gtk.CheckButton().new_with_label("On battery")
        self.suspend_on_powersource = Gtk.CheckButton().new_with_label("On power source")
        self.suspend_on_grid = Gtk.Grid()
        self.suspend_on_grid.props.halign = Gtk.Align.START
        self.suspend_on_grid.props.column_spacing = 10
        self.suspend_on_grid.attach(self.suspend_on_battery, 0, 0, 1, 1)
        self.suspend_on_grid.attach(self.suspend_on_powersource, 1, 0, 1, 1)

        self.suspend_delay = Gtk.SpinButton().new_with_range(min=5, max=3600, step=1)
        suspend_delay_label = Gtk.Label("Delay (seconds)")
        self.suspend_delay_grid = Gtk.Grid()
        self.suspend_delay_grid.props.halign = Gtk.Align.START
        self.suspend_delay_grid.props.column_spacing = 10
        self.suspend_delay_grid.attach(self.suspend_delay, 0, 0, 1, 1)
        self.suspend_delay_grid.attach(suspend_delay_label, 1, 0, 1, 1)

        self.resume_label = Gtk.Label("Resume: ")
        self.resume_label.props.expand = True
        self.resume_label.props.margin_top = 5
        self.resume_label.props.halign = Gtk.Align.END
        self.resume_label.props.valign = Gtk.Align.START
 
        self.resume_delay = Gtk.SpinButton().new_with_range(min=5, max=3600, step=1)
        self.resume_on = Gtk.CheckButton().new_with_label("On activate window")
        resume_delay_label = Gtk.Label("Delay (seconds)")
        self.resume_grid = Gtk.Grid()
        self.resume_grid.props.column_spacing = 10
        self.resume_grid.props.row_spacing = 10
        self.resume_grid.props.halign = Gtk.Align.START
        self.resume_grid.attach(self.resume_delay, 0, 0, 1, 1)
        self.resume_grid.attach(resume_delay_label, 1, 0, 1, 1)
        self.resume_grid.attach(self.resume_on, 0, 1, 2, 1)

        self.settings_label = Gtk.Label("Settings: ")
        self.settings_label.props.expand = True
        # self.settings_label.props.margin_top = 5
        self.settings_label.props.halign = Gtk.Align.END
        self.settings_label.props.valign = Gtk.Align.START

        self.persistent = Gtk.CheckButton().new_with_label("Persistent on relaunch")

        self.grid_bottom = Gtk.Grid()
        self.grid_bottom.props.column_spacing = 10
        self.grid_bottom.props.row_spacing = 15
        self.grid_bottom.props.hexpand = True
        self.grid_bottom.props.halign = Gtk.Align.START

        self.grid_bottom.attach(enable_label, 0, 0, 1, 1)
        self.grid_bottom.attach(self.enable_suspend, 1, 0, 1, 1)

        self.grid_bottom.attach(self.suspend_label, 0, 1, 1, 2)
        self.grid_bottom.attach(self.suspend_delay_grid, 1, 1, 2, 1)
        self.grid_bottom.attach(self.suspend_on_grid, 1, 2, 1, 1)

        self.grid_bottom.attach(self.resume_label, 0, 3, 1, 1)
        self.grid_bottom.attach(self.resume_grid, 1, 3, 2, 1)

        self.grid_bottom.attach(self.settings_label, 0, 4, 1, 1)
        self.grid_bottom.attach(self.persistent, 1, 4, 2, 1)

        grid = Gtk.Grid()
        grid.props.name = "app-list-item-bottom"
        grid.attach(self.grid_bottom, 0, 0, 1, 1)

        self.revealer = Gtk.Revealer()
        self.revealer.props.hexpand = True
        self.revealer.add(grid)

        self.attach(self.grid_top, 0, 0, 1, 1)
        self.attach(self.revealer, 0, 1, 1, 1)

        if not self.app_object.enable_suspend:
            self.suspend_label.props.sensitive = False
            self.suspend_delay_grid.props.sensitive = False
            self.suspend_on_grid.props.sensitive = False
            self.resume_label.props.sensitive = False
            self.resume_grid.props.sensitive = False
            self.settings_label.props.sensitive = False
            self.persistent.props.sensitive = False

    def toggle_enable_suspend(self, switch, active):
        main_window = self.get_toplevel()
        app = main_window.app
        if switch.get_active():
            self.suspend_label.props.sensitive = True
            self.suspend_delay_grid.props.sensitive = True
            self.suspend_on_grid.props.sensitive = True
            self.resume_label.props.sensitive = True
            self.resume_grid.props.sensitive = True
            self.settings_label.props.sensitive = True
            self.persistent.props.sensitive = True
            self.app_object.enable_suspend = True
            # app.apps_manager.last_running_apps[self.app_object.name].enable_suspend = True
        else:
            self.suspend_label.props.sensitive = False
            self.suspend_delay_grid.props.sensitive = False
            self.suspend_on_grid.props.sensitive = False
            self.resume_label.props.sensitive = False
            self.resume_grid.props.sensitive = False
            self.settings_label.props.sensitive = False
            self.persistent.props.sensitive = False
            self.app_object.enable_suspend = False
            # app.apps_manager.last_running_apps[self.app_object.name].enable_suspend = False
        print("self.app_object.enable_suspend", self.app_object.enable_suspend)
        print("app.apps_manager.last_running_apps[self.app_object.name].enable_suspend", app.apps_manager.last_running_apps[self.app_object.name].enable_suspend)
        print("switch", switch.get_active())

    def toggle_app_settings(self):
        if self.revealer.get_child_revealed():
            self.revealer.set_reveal_child(False)
        else:
            self.revealer.set_reveal_child(True)
        main_window = self.get_toplevel()
        app = main_window.app

        print("self.app_object.enable_suspend", self.app_object.enable_suspend)
        print("app.apps_manager.last_running_apps[self.app_object.name].enable_suspend", app.apps_manager.last_running_apps[self.app_object.name].enable_suspend)
