#!/usr/bin/env python3

'''
   Copyright 2020 Adi Hezral (hezral@gmail.com) (https://github.com/hezral)

   This file is part of Movens.

    Movens is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Movens is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Movens.  If not, see <http://www.gnu.org/licenses/>.
'''
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