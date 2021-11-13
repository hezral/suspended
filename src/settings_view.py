# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio,  GObject


#------------------CLASS-SEPARATOR------------------#


class SettingsView(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #-- object ----#
        gio_settings = Gio.Settings(schema_id="com.github.hezral.suspended")
        gtk_settings = Gtk.Settings().get_default()

        # #-- settings --------#
        # #------ theme switch ----#
        # theme_switch = SubSettings(name="theme-switch", label="Switch between Dark/Light theme", sublabel=None, separator=False)
        # theme_switch.switch.bind_property("active", gtk_settings, "gtk_application_prefer_dark_theme", GObject.BindingFlags.SYNC_CREATE)
        # gio_settings.bind("prefer-dark-style", theme_switch.switch, "active", Gio.SettingsBindFlags.DEFAULT)


        #-- settings items grid --------#
        grid = Gtk.Grid()
        grid.props.margin = 8
        grid.props.hexpand = True
        grid.props.row_spacing = 8
        grid.props.column_spacing = 10
        # grid.attach(theme_switch, 0, 1, 1, 1)

        #-- settings items frame --------#
        frame = Gtk.Frame()
        frame.get_style_context().add_class("settings-frame")
        frame.add(grid)



        #-- SettingsView construct--------#
        self.props.name = "settings-view"
        self.get_style_context().add_class(self.props.name)
        self.props.expand = True
        self.props.margin = 20
        self.props.margin_top = 12
        self.props.row_spacing = 6
        self.props.column_spacing = 6
        self.attach(frame, 0, 1, 1, 1)


    def generate_separator(self):
        separator = Gtk.Separator()
        separator.props.hexpand = True
        separator.props.valign = Gtk.Align.CENTER
        return separator

    def on_switch_activated(self, switch, gparam):
        name = switch.get_name()

        if self.is_visible():
            stack = self.get_parent()
            window = stack.get_parent()
            if name == "persistent-mode":
                if switch.get_active():
                    #print('state-flags-on')
                    window.disconnect_by_func(window.on_persistent_mode)
                else:
                    window.connect("state-flags-changed", window.on_persistent_mode)
                    #print('state-flags-off')
            if name == "sticky-mode":
                if switch.get_active():
                    window.stick()
                else:
                    window.unstick()


#------------------CLASS-SEPARATOR------------------#


class SubSettings(Gtk.Grid):
    def __init__(self, name, label, sublabel=None, separator=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        #------ box--------#
        box = Gtk.VBox()
        box.props.spacing = 2
        box.props.hexpand = True

        #------ label--------#
        label = Gtk.Label(label)
        label.props.halign = Gtk.Align.START
        box.add(label)
        
        #------ sublabel--------#
        if sublabel is not None:
            sublabel = Gtk.Label(sublabel)
            sublabel.props.halign = Gtk.Align.START
            sublabel.get_style_context().add_class("settings-sub-label")
            box.add(sublabel)

        #------ switch--------#
        self.switch = Gtk.Switch()
        self.switch.props.name = name
        self.switch.props.halign = Gtk.Align.END
        self.switch.props.valign = Gtk.Align.CENTER
        self.switch.props.hexpand = False

        #------ separator --------#
        if separator:
            row_separator = Gtk.Separator()
            row_separator.props.hexpand = True
            row_separator.props.valign = Gtk.Align.CENTER
            self.attach(row_separator, 0, 3, 2, 1)
        
        #-- SubSettings construct--------#
        self.props.name = name
        self.props.hexpand = True
        self.props.row_spacing = 8
        self.props.column_spacing = 10
        self.attach(box, 0, 1, 1, 2)
        self.attach(self.switch, 1, 1, 1, 2)
