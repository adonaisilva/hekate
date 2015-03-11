#!/usr/bin/env python
#-*- coding: utf-8 -*-
import pygtk
pygtk.require('2.0')
import gtk, sys
from multiprocessing import Pipe
from time import sleep
from gui_widgets import panel_cameraSelector, panel_cameraConfigurator, binary_images
from gui_dialogs import simulation
from api_process import permanent_shooter_tester, permanent_shooter
from api_capture import triangulator
from api_files import config_file

#GUI section 
class tester(object):
    def __init__(self, default_file = None, project_file = None):
        '''
        Add panels in object.main_frame
        '''
        self.__names_cameras = ["front", "side", "top"]
        self.__control_pipe, _control_pipe = Pipe()
        self.__sending_pipe, _sending_pipe = Pipe()
        self.__process_tester = permanent_shooter_tester(_control_pipe, _sending_pipe)
        self.__process_tester.start()
        self.__default_file = default_file
        self.__project_file = project_file
        self.__control_pipe.send(True)
        self.__camera_clicked = None
        #if loaded from another ("plugged") program, create a plug instead of a top level window 
        Wid = 0L
        if len(sys.argv) > 1:
            Wid = long(sys.argv[1])
            self.main_window = gtk.Plug(Wid)
        else:                  
            self.main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.main_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.main_window.set_border_width(10)
        self.main_window.set_resizable(False)
        'Create main table where all widgets are loaded'
        self.__main_table = gtk.Table(2, 4 ,False)
        self.__main_table.set_col_spacings(7)
        'Create pack elements and packing for frame "cameras"' 
        #frame where cameras are loaded
        self.__frame_view = gtk.Frame("")
        self.__frame_view.set_label_align(1.0, 0.5)
        self.__button_save = gtk.Button("Save")
        self.__button_cancel = gtk.Button('Return') 
        self.__main_table.attach(self.__frame_view, 0, 4, 0, 1, gtk.SHRINK, gtk.SHRINK)
        self.__main_table.attach(self.__button_save, 2, 3, 1, 2, gtk.FILL, gtk.FILL)
        self.__main_table.attach(self.__button_cancel, 3, 4, 1, 2, gtk.FILL, gtk.FILL)
        self.main_window.add(self.__main_table)   
        'Connect signals'
        self.__button_save.connect('clicked', self.__on_save)
        self.__button_cancel.connect('clicked', self.__on_cancel)
        self.main_window.connect('destroy', self.__del__)
        'Show'
        self.__create_panels()
        self.__load_panels()
        self.__idle = gtk.idle_add(self.__on_idle)
        self.main_window.show_all()
        return
    
    def __del__(self, widget = None):
        self.__main_quit(None)
        return
     
    def __main_quit(self, widget = None):
        gtk.idle_remove(self.__idle)
        sleep(.3)
        while self.__sending_pipe.poll():
            self.__sending_pipe.recv() 
        self.__control_pipe.send(-1)
        self.main_window.destroy()
        gtk.main_quit()
        return
    
    def __on_idle(self):
        if self.__current_panel != self.__load_panel:
            self.__load_panels()
        if self.__camera_clicked != None:
            self.__load_panel = True
            self.__panels[True](self.__camera_clicked)
        if self.__camera_clicked == None:
            self.__panels[True].reset()
            self.__load_panel = False
            self.__camera_clicked = self.__panels[False]()
        if not(self.__current_panel):
            for number, name in enumerate(self.__names_cameras):
                self.__panels[False].test_completion(name, number)
        return gtk.TRUE
    
    def __on_save(self, widget = None):
        if self.__current_panel == True:
            cameras_selected, camera_clicked = self.__panels[False].get_cameraConfig()
            config = [cameras_selected[camera_clicked] - 1] + self.__panels[True].get_config()
            self.__project_file.write("as is", "cameras", self.__names_cameras[camera_clicked], config)
            self.__project_file.write('list', "colors", self.__names_cameras[camera_clicked], self.__panels[True].get_color())
        return

    def __on_cancel(self, widget = None):
        if self.__current_panel == True:
            self.__camera_clicked = None
            self.__load_panel = False
            self.__panels[False].reset()
        if self.__current_panel == False:
            self.__del__()
        return    
    
    def __create_panels(self):
        'create all the panels, they will be loaded as needed'
        self.__panels = range(2)
        self.__panels[0] = panel_cameraSelector(self.__control_pipe, self.__sending_pipe, self.__default_file, self.__project_file)
        self.__panels[1] = panel_cameraConfigurator(self.__control_pipe, self.__sending_pipe, self.__default_file, self.__project_file)
        self.__load_panel = False
        self.__current_panel = False
        return
    
    def __load_panels(self):
        'loads the correct panel in the main window'
        self.__current_panel = self.__load_panel
        frame_labels = ("Cameras preview", self.__names_cameras[self.__camera_clicked if self.__camera_clicked != None else 0] + " Camera Configuration")
        self.__frame_view.set_label(frame_labels[self.__current_panel])
        #if there is a loaded panel then remove it and load the current needed panel
        if self.__frame_view.get_child() != None:
            self.__frame_view.remove(self.__frame_view.get_child())
        self.__frame_view.add(self.__panels[self.__current_panel].main_widget)
        return
    

class recorder(object):
    def __init__(self, default_file, project_file):
        self.__p_file = project_file
        self.__d_file = default_file
        units = range(2)
        units[0] = self.__p_file.read('str', 'units', 'length')[0]
        units[1] = self.__p_file.read('str', 'units', 'mass')[0]
        user_height = self.__p_file.read('list', 'user', 'height')
        self.__resolution = self.__p_file.read('list', 'cameras', 'resolution')
        self.__cameras_names = self.__d_file.read('str', 'cameras', 'names')
        self.__distances = [self.__p_file.read('list', 'geometry', cam) for cam in self.__cameras_names]
        self.__focal = [self.__p_file.read('list', 'focal', cam) for cam in self.__cameras_names]
        self.__control_pipe, self.control_pipe = Pipe()
        self.__sync_pipe, self.sync_pipe = Pipe()
        self.__triangulator = triangulator(self.__resolution, self.__distances, self.__focal, user_height)
        #if loaded from another ("plugged") program, create a plug instead of a top level window 
        Wid = 0L
        if len(sys.argv) > 1:
            Wid = long(sys.argv[1])
            self.main_window = gtk.Plug(Wid)
        else:                  
            self.main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.main_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.main_window.set_border_width(10)
        self.main_window.set_resizable(False) 
        
        self.check_manual = gtk.CheckButton("Manual operation")
        self.check_program = gtk.CheckButton("Programming")
        self.label_inter = gtk.Label("Interpolation:")
        self.combo_inter = gtk.combo_box_new_text()
        self.button_play = gtk.ToggleButton()
        self.button_stop = gtk.Button()
        self.button_open = gtk.Button()
        self.check_simulation = gtk.CheckButton("Show simulation")
        self.__binary = binary_images(self.__resolution, self.__cameras_names)
        self.__simulation = simulation(self, user_height, units)
        
        'Create pack elements and packing'
        
        self.frame_control = gtk.Frame("Controls")
        self.table_control = gtk.Table(7, 2, False)
        #Controls
        self.table_control.attach(self.check_manual, 0, 2, 0, 1, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.check_program, 0, 2, 1, 2, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.label_inter, 0, 2, 2, 3, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.combo_inter, 0, 2, 3, 4, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.button_play, 0, 1, 4, 5, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.button_stop, 1, 2, 4, 5, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.button_open, 0, 2, 5, 6, gtk.FILL, gtk.SHRINK)
        self.table_control.attach(self.check_simulation, 0, 2, 6, 7, gtk.FILL, gtk.SHRINK)
        
        self.table_control.set_border_width(10)
        self.table_control.set_row_spacings(5)
        self.table_control.set_col_spacings(5)
        self.table_control.set_row_spacing(1, 15)
        self.table_control.set_row_spacing(3, 15)
        self.table_control.set_row_spacing(5, 15)
        #Cameras
        self.frame_control.add(self.table_control)
        self.main_table = gtk.Table(2, 2, False)
        self.main_table.attach(self.frame_control, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        self.main_table.attach(self.__binary.main_widget, 1, 2, 0, 1, gtk.FILL, gtk.SHRINK)

        self.main_window.add(self.main_table)
        'Connect signals'
        self.main_window.connect('destroy', self.__main_quit)   
        self.button_play.connect('toggled', self.__on_toggle)  
        self.button_stop.connect('clicked', self.__on_stop)
        self.check_simulation.connect('toggled', self.__on_check_visibility)
        self.check_simulation.set_active(True)
        'Initial configuration'
        self.button_play.set_image(self.__set_play())
        self.button_stop.set_image(self.__set_stop())
        self.button_open.set_image(self.__set_open())  
        'Show'
        self.main_window.show_all()
        return      
        
    def __set_play(self, mode = False):
        image = gtk.Image()
        image.set_from_stock((gtk.STOCK_MEDIA_RECORD, gtk.STOCK_MEDIA_PAUSE)[mode], gtk.ICON_SIZE_BUTTON) 
        return image
    
    def __set_stop(self):
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON)
        return image   
    
    def __set_open(self):
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        return image
    
    def __on_check_visibility(self, widget):
        if self.__simulation.get_visible() != self.check_simulation.get_active():
            self.__simulation.set_visible(data = self.check_simulation.get_active()) 
        return
    
    def __on_toggle(self, widget, data = None):
        if self.button_play.get_active():
            self.__idle = gtk.idle_add(self.__on_idle)
            while self.__sync_pipe.poll():
                self.__sync_pipe.recv()
            self.__sync_pipe.send(1)
        else:
            gtk.idle_remove(self.__idle)
            sleep(.3)
            while self.__sync_pipe.poll():
                self.__sync_pipe.recv() 
        self.button_play.set_image(self.__set_play(self.button_play.get_active()))
        return

    def __on_stop(self, widget):
        self.button_play.set_active(False)
        return

    def __on_idle(self):
        if self.__sync_pipe.poll():
            results = self.__sync_pipe.recv()
            self.__sync_pipe.send(1)
            if self.__binary.can_draw():
                self.__binary([results[index][1] for index in xrange(3)])
            coordinates = self.__triangulator(results)
            print coordinates
        return gtk.TRUE if self.button_play.get_active() else gtk.FALSE
    
    def __del__(self):
        self.__main_quit(None)
        return
    
    def __main_quit(self, widget):
        try:
            gtk.idle_remove(self.__idle)
        except:
            pass
        sleep(.3)
        while self.__sync_pipe.poll():
            self.__sync_pipe.recv() 
        self.__control_pipe.send(-1)
        gtk.main_quit()
        return


#Function section
def main(data):
    data = int(data)
    default_file = config_file(sys.argv[3]+ '/.default')
    project_file = config_file(sys.argv[3]+ '/.project')
    if data == 0:
        app = tester(default_file, project_file)
    elif data == 1:
        app = recorder(default_file, project_file)
        pro = permanent_shooter(app.control_pipe, app.sync_pipe, default_file, project_file)
        pro.start()
    return
      
if __name__ == "__main__":
    main(sys.argv[2])
    gtk.main()