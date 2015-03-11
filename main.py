#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    hékate - Human-machine interface by computer vision for programming 
    and operation of a virtual anthropomorphic robot.

    Copyright (C) 2012-2014  Edgar Adonai Silva Calderón

This file is part of hékate.

    hékate is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    hékate is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with hékate.  If not, see <http://www.gnu.org/licenses/>.
'''
'''
Cross-module variables:
                        __builtin__.MOD_PATH = modules path
                        __builtin__.MEDIA_PATH = media path
                        __builtin__.MAIN_PATH = main path
                        __builtin__.META = Metadata XML root
'''
#needed for importing
import os, sys, inspect, __builtin__
from xml.etree.ElementTree import parse
#create dictionary with folder names and variable name
subfolders = {"resources":"MEDIA_PATH", "modules":"MOD_PATH"}
# realpath() with make your script run, even if you symlink it :)
temp = os.path.split(inspect.getfile(inspect.currentframe() ))[0]
cmd_folder = os.path.realpath(os.path.abspath(temp))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
# use this if you want to include modules from a subfolder
for sub in subfolders:
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(temp,sub)))
    exec "%s=%s" %(("__builtin__." + subfolders[sub]), "cmd_subfolder")
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
__builtin__.MAIN_PATH = cmd_folder
#retrieve metadata
META = parse("resources/meta.xml").getroot()
__title__ = META.find("./title").text
__author__ = META.find("./author").text
__copyright__ = META.find("./copyright").text
__license__ = META.find("./license").text
__date__ = META.find("./date").text
__version__ = META.find("./version").text
__status__ = META.find("./status").text
__email__ = META.find("./email").text
__builtin__.METADATA = META
#Let's go
from gui_main import start      
if __name__ == "__main__":
    start()