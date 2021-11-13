# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import os
import configparser
from gi.repository import GLib

#------------------CLASS-SEPARATOR------------------#


class ConfigManager():
    
    config = configparser.ConfigParser()
    conf_file = os.path.join(GLib.get_user_config_dir(), 'xsuspender.conf')
    conf_file = "/usr/share/doc/xsuspender/examples/xsuspender.conf"
    conf_file = "/home/adi/.local/share/applications/appeditor-local-application-1.desktop"

    def __init__(self, gtk_application, *args, **kwargs):

        # initialize config_file if doesn't exist
        try:
            f = open(self.conf_file)
            f.close()
        except FileNotFoundError:
            with open(self.conf_file, 'w') as fp: 
                pass
        finally:
            self.config.read(self.conf_file)

        sections = self.config.sections()

        for section in sections:

            # Default configurations
            if section == "Default":
                for option in self.config.options(section):
                    print(section, option, "=", self.config.get(section, option))

            print("------------------------------")

            # App specific configurations
            if section != "Default":
                for option in self.config.options(section):
                    print(section, option, "=", self.config.get(section, option))

        pass

    def write_conf(self, app_info):
        pass

    def read_conf(self, app_info):
        pass



configs_manager = ConfigManager(gtk_application=None)