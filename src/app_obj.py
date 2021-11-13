# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from dataclasses import dataclass, field, fields
from typing import Any

import re

from . import utils

proc_states = {}
proc_states["S"] = "Active"
proc_states["T"] = "Suspended"
proc_states["Z"] = "Zombie"
proc_states["R"] = "Runnable"
proc_states["D"] = "Uninterruptable"

@dataclass
class AppObject:
    name: str = ""
    icon: str = ""
    startup_wm_class: str = ""
    no_display: bool = False
    desktop_file: str = ""
    app_exec: str = ""
    flatpak: bool = False
    wm_class: str = ""
    wm_name: str = ""
    workspace_n: str = ""
    window_id: int = 0
    pid: str = ""
    # pids: list = field(default_factory=list)
    proc_state: str = ""
    proc_state_name: str = ""
    persistent_on_relaunch: bool = False
    suspend_delay: int = 0 # seconds before suspending
    suspend_on_battery: bool = False
    suspend_on_powersource: bool = False
    resume_every: int = 60 # seconds for cycling resume
    resume_on_activate_window: bool = True
    suspended_timestamp: str = ""
    suspended: bool = False
    enable_suspend: bool = False

    def __post_init__(self):
        if self.flatpak:
            if "--file-forwarding" in self.app_exec:
                app_id = re.search("--file-forwarding\s(?P<name>.+)*", self.app_exec).group(1).split(" ")[0]
            else:
                try:
                    app_id = re.search("--command=(?P<name>.+)", self.app_exec).group(1).split(" ")[1]
                except:
                    app_id = re.search("--command=(?P<name>.+)", self.app_exec).group(1).split(" ")[0]

            self.pid = utils.get_flatpak_pid(app_id)

        # print(self.name, self.flatpak, self.pid, self.proc_state, self.proc_state_name)
        if self.pid:
            self.proc_state = utils.parse_proc_state(utils.read_stat_file(self.pid))
            self.proc_state_name = proc_states[self.proc_state]
