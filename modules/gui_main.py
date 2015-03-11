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
import pygtk
pygtk.require('2.0')
import gtk, __builtin__
from cv2 import VideoCapture
from os import system
from gui_dialogs import splash, about, select_project, create_project, default_values

class main_gui(object):
    '''
    
    '''
    def __init__(self, found):
        '''
        
        '''
        #Save Arguments
        self.__found = found
        #Load variables
        self.__working_dir = None
        self.__flag = True
        #Main window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_resizable(False)
        self.window.set_title(__builtin__.METADATA.find("./title").text+\
                              " v"+__builtin__.METADATA.find("./version").text)
        #Menu Bar
        menuBar = gtk.MenuBar()
        #File Menu Items
        menu_file = gtk.Menu()
        item_exit = gtk.MenuItem("Close")
        menu_file.append(item_exit)
        #Edit Menu Items
        menu_edit = gtk.Menu()
        item_default = gtk.MenuItem("Default values")
        menu_edit.append(item_default)
        #Help Menu Items
        menu_help = gtk.Menu()
        item_help = gtk.MenuItem("Help Contents")
        item_about = gtk.MenuItem("About")
        menu_help.append(item_help)
        menu_help.append(gtk.SeparatorMenuItem())
        menu_help.append(item_about)
        #Menu Bar elements
        subMenu_file = gtk.MenuItem("File")
        subMenu_file.set_submenu(menu_file) 
        subMenu_edit = gtk.MenuItem("Edit")
        subMenu_edit.set_submenu(menu_edit)
        subMenu_help = gtk.MenuItem("Help")
        subMenu_help.set_right_justified(True)
        subMenu_help.set_submenu(menu_help)
        #Menu Packaging
        menuBar.append(subMenu_file)
        menuBar.append(subMenu_edit)
        menuBar.append(subMenu_help)    
        #Main items for packaging
        box = gtk.VBox(0, 0)
        self.__panel = gtk.Frame("")
        self.__panel.set_border_width(10)
        box.pack_start(menuBar,False, False, 0)
        box.pack_start(self.__panel,False, False, 0)
        #Button items (they change as the selected options)
        self.__table_buttons = gtk.Table(2, 3, False)
        self.__table_buttons.set_col_spacings(30)
        self.__buttons_options = [gtk.Button() for i in range(3)]
        self.__images_options = [gtk.Image() for i in range(3)]
        self.__labels_options = [gtk.Label() for i in range(3)]
        for i, (button, image, label) in enumerate(zip(self.__buttons_options, self.__images_options, self.__labels_options)):
            self.__table_buttons.attach(button ,i, i+1, 0, 1, gtk.SHRINK, gtk.SHRINK)
            self.__table_buttons.attach(label ,i, i+1, 1, 2, gtk.SHRINK, gtk.SHRINK)
            button.add(image)
        self.__panel.add(self.__table_buttons)
        #connect buttons
        self.__handler_idsButton = [None] * 3
        self.__handler_idsButton[0] = self.__buttons_options[0].connect('clicked', self.__new_project)
        self.__handler_idsButton[1] = self.__buttons_options[1].connect('clicked', self.__main_quit)
        self.__handler_idsButton[2] = self.__buttons_options[2].connect('clicked', self.__open_project) 
        #connect main signals
        item_about.connect("activate", about)
        item_exit.connect("activate", self.__main_quit)
        item_default.connect("activate", self.__set_default)
        self.window.connect("destroy", self.__main_quit)
        self.__idle = gtk.idle_add(self.__on_idle)
        #show items      
        self.window.add(box)
        self.window.show_all()
        return
    
    def __main_quit(self, widget, event = None):
        '''
        
        '''
        #When the window is destroyed, kill all python instances
        gtk.main_quit()
        #TODO: Search a proper way to kill interpreter instances.
        system('killall python')
        return
    
    def __on_idle(self, data = None):
        '''
        
        '''
        if (self.__flag != True) and (self.__working_dir != None):
            if 'None' in open(self.__working_dir + "/.project.cfg").read():
                self.__buttons_options[1].set_sensitive(False)
            else:
                self.__buttons_options[1].set_sensitive(True)
        if self.__flag != self.__working_dir:
            self.__flag = self.__working_dir
            self.__set_buttons()
        return gtk.TRUE
    
    def __plug_removed(self, widget = None):
        '''
        
        '''
        if self.__panel.child != None:
            self.__panel.remove(self.__panel.get_child())
        self.__panel.add(self.__table_buttons)
        return
    
    def __new_project(self, widget):
        '''
        
        '''
        self.__working_dir = create_project()
        return
                
    def __open_project(self, widget):
        '''
        
        '''
        self.__working_dir = select_project()
        return   

    def __set_buttons(self, widget = None):
        '''
        
        '''
        labels = (("New Project", "", "Edit Project"), ("Configuration", "Recording", "Recalculate"))
        icons = (("new_project", "new_project", "edit_project"), ("configure", "record", "recalculate"))
        x = 0 if self.__working_dir == None else 1
        for i, (image, label) in enumerate(zip(self.__images_options, self.__labels_options)):
            source = __builtin__.MEDIA_PATH + "/" + icons[x][i] + ".png"
            image.set_from_file(source)
            label.set_text(labels[x][i])
        self.__buttons_options[1].set_visible(x) 
        if x:
            for i, button in enumerate(self.__buttons_options):
                button.handler_disconnect(self.__handler_idsButton[i])
                self.__handler_idsButton[i] = button.connect('clicked', self.__load_panel, i)
        return
                    
    def __load_panel(self, widget, panel):
        '''
        
        '''
        if self.__panel.child != None:
            self.__panel.remove(self.__panel.get_child())
            try:
                del self.__socket
            except:
                pass
        self.__socket = gtk.Socket()
        self.__socket.connect("plug-removed", self.__plug_removed)
        self.__socket.show()
        self.__panel.add(self.__socket)
        self.__socket_id = self.__socket.get_id()
        system("python ./modules/gui_sockets.py " + str(self.__socket_id) + " " + str(panel) + " " +
               self.__working_dir + " &")
        self.__panel.show_all()
        return
       
    def __set_default(self, widget, data = None):
        '''
        
        '''
        try:
            default_values(self.__working_dir + "/.default")
        except:
            default_values(__builtin__.MEDIA_PATH + "/default")
        return


def start():
    '''
    
    '''
    #Load splash screen
    splScr = splash()
    found = []
    #find connected cameras        
    for num in range(10):
        cam = VideoCapture(num)
        cam.open
        #show progress bar 'movement' while the main program find cameras
        splScr.update()
        if not cam.read()[0]:
            del(cam)
        else:
            cam.release()
            found.append(num)
        while gtk.events_pending():
            gtk.main_iteration()
    #destroy splash screen when all cameras are finded
    splScr.destroy()
    print 'connected cameras:', len(found)
    #run main program
    main_gui(found)
    gtk.main()
    return