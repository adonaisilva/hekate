#!/usr/bin/env python
#-*- coding: utf-8 -*-
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
from csv import DictWriter, excel
from ConfigParser import RawConfigParser
from types import StringType
from numpy import array, uint8

class csv_writer():
    def __init__(self, filename):
        self.__fields = ('Position', 'Velocity', 'Acceleration', 'Torque')
        self.__links = ('SHOULDER_X', 'SHOULDER_Y', 'SHOULDER_Z', 'ELBOW_Z')
        self.__fieldnames = []
        for field in self.__fields:
            for link in self.__links:
                self.__fieldnames.append(field + " " + link)
        self.__fieldnames.append('Time')
        self.__headers = dict( (n, n) for n in self.__fieldnames)
        self.__filename = str(filename)+".xls"
        self.__file = open(self.__filename, 'wt')
        self.__writer = DictWriter(self.__file, dialect = excel, fieldnames = self.__fieldnames) 
        self.__writer.writerow(self.__headers)
        return

    def __call__(self, values, d_time):
        data = {}
        for index in xrange(4):
            for l_index in xrange(4):
                if index == 0:
                    data[self.__fieldnames[index*4+l_index]] = values.position[l_index]
                elif index == 1:
                    data[self.__fieldnames[index*4+l_index]] = values.velocity[l_index]
                elif index == 2:
                    data[self.__fieldnames[index*4+l_index]] = values.acceleration[l_index]
                elif index == 3:
                    data[self.__fieldnames[index*4+l_index]] = values.torque[l_index]
        data[self.__fieldnames[-1]] = d_time
        self.__writer.writerow(data)
        return
        
    def __del__(self):
        self.close_file()
        return
    
    def close_file(self):
        self.__file.close()
        return

class config_file(object):
    def __init__(self, filename):
        self.__filename = filename + ".cfg"
        self.__file = RawConfigParser()
        self.__file.read(self.__filename)
        return
    
    def read(self, data_type, section, value):
        if data_type == 'list':
            temp  = self.__file.get(section, value)
            if type(temp) != StringType:
                return eval(str(temp), {}, {})
            return eval(temp, {}, {})
        if data_type == 'str':
            string = self.__file.get(section, value)
            string = string.replace('[', '').replace(']', '')
            strings = (string[0:len(string)]).split(", ")
            return  strings if strings[0] != '' else string
        if data_type == 'np_array':
            color = self.read('list', section, value)
            return [array(col, uint8) for col in color]
        return self.__file.get(section, value)
    
    def write(self, data_type, section, value, data):
        if data_type == 'list':
            temp = []
            for x in data:
                temp.append(x.tolist())
            data = temp
        self.__file.set(section, value, data)
        with open(self.__filename, 'wb') as _file:
            self.__file.write(_file)
        return
        
        
        
        