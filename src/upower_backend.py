# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import os

from pydbus import SessionBus, SystemBus
from gi.repository import GObject, Gio

class UpowerBackend(GObject.GObject):
    def __init__(self):
        GObject.GObject.__init__(self)

        self.bus = SystemBus()
        # self.proxy = self.bus.get("org.freedesktop.UPower", "/org/freedesktop/UPower")
        self.proxy = self.bus.get(".UPower")

    def is_on_battery(self):
        print(self.proxy.OnBattery)

    def is_lid_closed(self):
        if self.proxy.LidIsPresent:
            print(self.proxy.LidIsClosed)


upower = UpowerBackend()

upower.is_on_battery()