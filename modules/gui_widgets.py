#!/usr/bin/env python
#-*- coding: utf-8 -*-


import pygtk
from modules.api_capture import camera
from compiler.syntax import check
pygtk.require('2.0')
import gtk
from gtk.gdkgl import MODE_RGB, MODE_DEPTH, MODE_DOUBLE, Config, NoMatches
from gtk.gtkgl import DrawingArea
from OpenGL.GL import (glClearColor, glClearDepth, glDepthFunc, glEnable, glViewport,
                       glMatrixMode, glLoadIdentity, glFrustum, glClear, glPushMatrix,
                       glRotatef, glTranslatef, glColor3f, glScalef, glPopMatrix, glFlush,
                       glBegin, glVertex3f, glEnd, glPolygonMode, GL_LESS, GL_DEPTH_TEST, 
                       GL_PROJECTION, GL_MODELVIEW, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
                       GL_FRONT_AND_BACK, GL_LINE, GL_QUADS, GL_LINE_SMOOTH, glLineWidth)
from OpenGL.GLU import gluLookAt
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.pyplot import figure, figlegend
from matplotlib import font_manager
from cv2 import resize, merge, cvtColor
from cv2.cv import CV_RGB2HSV
from numpy import diff, array, zeros, uint8
from math import sin, cos, pi
from types import NoneType
from api_capture import thresholder, segment_pool, filter_pool
from api_values import masked_image


class panel_cameraSelector(object):
    def __init__(self, control_pipe, sending_pipe, default_file = None, project_file = None, entry_list = ["1","2","3"]):
        '''
        Panel where the user can match a camera with his position, then select segmentation configuration
        for each one. It saves all data in project file. 
        
            control_pipe: pipe ending for control the permanent_shooterTester
            sending_pipe: pipe ending for data transmission from the permanent_shooterTester
            default_file: file where the default stored values 
            project_file: file with the project stored data
            entry_list:   list of cameras detected  
        
        '''
        self.__control_pipe = control_pipe
        self.__sending_pipe = sending_pipe
        self.__names_cameras = ["Front", "Side", "Top"]
        self.__cameras_selected = [0] * 3
        self.__camera_clicked = None
        self.__file_default = default_file
        self.__file_project = project_file
        #main table where camera buttons are loaded
        self.main_widget = gtk.Table(2, 2 ,True)
        self.main_widget.set_row_spacings(10)
        self.main_widget.set_col_spacings(10)
        #button for system (geometry) configuration
        self.__button_project = gtk.Button()
        self.__icon_project = gtk.Image()
        label = gtk.Label("Project data")
        hbox = gtk.HBox(spacing = 10)
        hbox.add(self.__icon_project)
        hbox.add(label)
        self.__button_project.add(hbox)
        self.__button_project.connect("clicked", self.__on_clickSystem)
        #button for each camera configuration
        self.__image_buttonCamera = [gtk.Image() for i in xrange(3)]
        self.__button_camera = [gtk.Button() for i in xrange(3)]
        for button, image in zip(self.__button_camera, self.__image_buttonCamera):
            button.connect("clicked", self.__on_clickCamera)
            image.set_size_request(320, 240)
            button.add(image)
        #table where the current cameras configuration status is shown
        self.__table_status = gtk.Table(7, 3, False)
        self.__alignment_tableStatus = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.5, yscale=0.05)
        #status elements
        self.__label_status = gtk.Label("Configuration status")
        self.__separator_status = gtk.HSeparator()
        self.__label_status.set_justify(gtk.JUSTIFY_CENTER)
        self.__label_status.set_alignment(0.5, 0.5)
        self.__image_statusCamera = range(3)
        self.__label_statusCamera = range(3)
        self.__combo_cameraSelector = range(3)
        #Setup a ComboBox or ComboBoxEntry based on a list of strings.           
        self.__model_full = gtk.ListStore(str)
        if not(isinstance(entry_list, list)):
            entry_list = list(entry_list)
        entry_list.insert(0, "Select Camera")
        self.__entries = entry_list
        for i in self.__entries:
            self.__model_full.append([i])
        self.__label_statusCamera = [gtk.Label(self.__names_cameras[i]+" camera") for i in xrange(3)]
        self.__combo_cameraSelector = [gtk.ComboBox() for i in xrange(3)]
        self.__image_statusCamera = [gtk.Image() for i in xrange(3)]
        for i, (combo, image, label) in enumerate(zip(self.__combo_cameraSelector, self.__image_statusCamera, self.__label_statusCamera)):
            combo.connect("changed", self.__on_changeCombo)
            combo.set_model(self.__model_full)
            cell = gtk.CellRendererText()
            combo.pack_start(cell, True)
            combo.add_attribute(cell, 'text', 0)
            combo.set_active(0)
            label.set_justify(gtk.JUSTIFY_LEFT)
            label.set_alignment(0.0, 0.5)
            self.__table_status.attach(combo, 0, 1, 2+i, 3+i)
            self.__table_status.attach(image, 1, 2, 2+i, 3+i)
            self.__table_status.attach(label, 2, 3, 2+i, 3+i)
        #pack status elements
        self.__table_status.attach(self.__label_status, 0, 3, 0, 1)
        self.__table_status.attach(self.__separator_status, 0, 3, 1, 2)
        self.__table_status.attach(self.__button_project, 0, 3, 5, 6, gtk.SHRINK, gtk.SHRINK)
        self.__table_status.set_row_spacings(2)
        self.__table_status.set_row_spacing(0, 3)
        self.__table_status.set_row_spacing(1, 7)
        self.__alignment_tableStatus.add(self.__table_status)
        #pack elements in table
        self.main_widget.attach(self.__alignment_tableStatus, 1, 2, 0, 1)
        self.main_widget.attach(self.__button_camera[2], 0, 1, 0, 1)
        self.main_widget.attach(self.__button_camera[1], 1, 2, 1, 2)
        self.main_widget.attach(self.__button_camera[0], 0, 1, 1, 2)  
        #show
        self.main_widget.show_all()
        return
    
    def __call__(self):
        if self.__sending_pipe.poll():
            self.__current_images = self.__sending_pipe.recv()
            self.__control_pipe.send(True)
            for i, image in enumerate(self.__image_buttonCamera):
                if self.__current_images[i] != None:
                    image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_array(self.__current_images[i], gtk.gdk.COLORSPACE_RGB, 8))
                else:
                    image.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_LARGE_TOOLBAR)
        return self.__camera_clicked
    
    def __on_changeCombo(self, widget):
        try:
            if widget.get_active() != 0:
                self.__cameras_selected.index(widget.get_active())
            else:
                raise Exception()
        except:
            self.__cameras_selected[self.__combo_cameraSelector.index(widget)] = widget.get_active()
            self.__sending_pipe.send([None if x == 0 else x-1 for x in self.__cameras_selected ])
            self.__activate_buttons(widget)
            return
        widget.set_active(0)
        message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        message.set_title("Camera already selected")
        message.set_markup("Select another camera")
        message.run()
        message.destroy()
        self.__activate_buttons(widget)
        return
        
    def __activate_buttons(self, widget):
        active = [None if x == 0 else x-1 for x in self.__cameras_selected ][self.__combo_cameraSelector.index(widget)]
        active = True if active != None else False
        self.__button_camera[self.__combo_cameraSelector.index(widget)].set_sensitive(active)
        return  

    def __on_clickCamera(self, widget = None):
        #self.__camera_clicked indicates the clicked button camera position, by convention: 0 front, 1 side, 2 top 
        self.__camera_clicked = widget.get_parent().get_children().index(widget)
        return
    
    def __on_clickSystem(self, widget = None):
        from gui_dialogs import project_values
        project_values(self.__file_default, self.__file_project)
        return
    
    def __change_statusImage(self, camera_id, status):
        'change the status image that indicates if a camera is fully configured'
        #camera_id is the index number for the image array 0-front, 1-side, 2-top
        #status indicate if the configuration is complete 0-incomplete, 1-complete
        __images_options = [gtk.STOCK_NO, gtk.STOCK_YES]
        self.__image_statusCamera[camera_id].set_from_stock(__images_options[status], gtk.ICON_SIZE_SMALL_TOOLBAR)
        return
    
    def get_cameraConfig(self):
        return self.__cameras_selected, self.__camera_clicked
    
    def test_completion(self, camera_name, camera_id):
        def TryNone(value):
            return None if str(value).find('None') != -1 else False
        complete = [False]
        complete += [TryNone(self.__file_project.read('list', 'cameras', 'resolution'))]
        complete += [TryNone(self.__file_project.read('list', 'cameras', camera_name))]
        complete += [TryNone(self.__file_project.read('list', 'colors', camera_name))]
        complete += [TryNone(self.__file_project.read('list', 'geometry', camera_name))]
        complete += [TryNone(self.__file_project.read('list', 'focal', camera_name))]
        if TryNone(complete) == False:
            self.__change_statusImage(camera_id, 1)
        else:
            self.__change_statusImage(camera_id, 0)
        return
    
    def reset(self):
        self.__camera_clicked = None
        return


class panel_cameraConfigurator(object):
    def __init__(self, control_pipe, sending_pipe, default_file = None, project_file = None):
        self.__request_draw = [False, 0]
        regions = ("Shoulder", "Elbow", "Wrist")
        colors = ("red","green","blue") 
        self.__file_default = default_file
        self.__file_project = project_file
        #Set adjustments from default configuration
        self.__set_defaults()
        'Create main elements for region selection' 
        self.__buttons_region = [gtk.ToggleButton() for i in xrange(3)]
        self.__checks_region = [gtk.CheckButton() for i in xrange(3)]
        self.__icons_region = [gtk.Image() for i in xrange(3)]
        for i, (button, check, icon) in enumerate(zip(self.__buttons_region, self.__checks_region, self.__icons_region)):
            label = gtk.Label(colors[i])
            label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(colors[i]))
            check.add(label)
            alignment = gtk.Alignment(0, 0, 0, 0)
            hbox = gtk.HBox(spacing = 10)
            label = gtk.Label(regions[i])
            alignment.add(hbox)
            hbox.add(icon)
            hbox.add(label)
            button.add(alignment)
        self.__set_icon('all', False)
        label_region = gtk.Label("Region")
        label_show = gtk.Label("Show?")
        'Create pack elements and packing'      
        self.__table_regionSelection = gtk.Table(4, 2, False)
        self.__table_regionSelection.set_border_width(15)
        self.__table_regionSelection.set_row_spacings(5)
        #Pack
        self.__table_regionSelection.attach(label_region, 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(label_show, 1, 2, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__buttons_region[0], 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__checks_region[0], 1, 2, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__buttons_region[1], 0, 1, 2, 3, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__checks_region[1], 1, 2, 2, 3, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__buttons_region[2], 0, 1, 3, 4, gtk.FILL, gtk.SHRINK)
        self.__table_regionSelection.attach(self.__checks_region[2], 1, 2, 3, 4, gtk.FILL, gtk.SHRINK)
        'Create main elements for processing variables selection'
        #First self.__frame_ (blur)alignment = gtk.Alignment(0, 0, 0, 0)
        self.__label_blur = gtk.Label("K-size")
        self.__spin_blur = gtk.SpinButton(self.__adjustment_ker, 0.0, 0)
        self.__label_sigma = gtk.Label("Sigma")
        self.__range_sigma = gtk.HScale(self.__adjustment_sig)
        self.__range_sigma.set_size_request(125, 40)
        self.__range_sigma.set_digits(0)
        self.__label_type = gtk.Label("Type")
        self.__combo_type = gtk.combo_box_entry_new_text()
        #Second self.__frame_ (morph)
        self.__label_morph = gtk.Label("K-size")
        self.__spin_morph = gtk.SpinButton(self.__adjustment_mor, 0.0, 0)
        self.__label_contour = gtk.Label("Draw filled")
        self.__combo_contour = gtk.combo_box_entry_new_text()
        #Third self.__frame_ (butterworth)
        self.__label_order = gtk.Label("Order")
        self.__spin_order = gtk.SpinButton(self.__adjustment_ord, 0, 0)  
        self.__label_freq = gtk.Label("Freq.")
        self.__range_freq = gtk.HScale(self.__adjustment_fre)
        self.__range_freq.set_size_request(125, 40)
        self.__range_freq.set_digits(2)
        self.__label_minim = gtk.Label("Minim")
        self.__spin_minim = gtk.SpinButton(self.__adjustment_min, 0, 0)
        #Restore button
        button_restore = gtk.Button("Restore defaults")
        'Create pack elements and packing'
        self.__table_configSelection = gtk.Table(4, 1, False)
        self.__frame__filter = gtk.Frame("Filter")
        self.__frame__morph = gtk.Frame("Morphology & contour")
        self.__frame__signal = gtk.Frame("Signal smoothing")
        self.__table_filter = gtk.Table(2, 4, False)
        self.__table_morph = gtk.Table(2, 2, False)
        self.__table_signal = gtk.Table(2, 3, False)
        #Pack filter elements
        self.__table_filter.attach(self.__label_blur, 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_filter.attach(self.__spin_blur, 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_filter.attach(self.__label_sigma, 1, 2, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_filter.attach(self.__range_sigma, 1, 2, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_filter.attach(self.__label_type, 0, 2, 2, 3, gtk.FILL, gtk.SHRINK)
        self.__table_filter.attach(self.__combo_type, 0, 2, 3, 4, gtk.EXPAND, gtk.SHRINK)
        #Pack morph elements        
        self.__table_morph.attach(self.__label_morph, 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_morph.attach(self.__label_contour, 1, 2, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_morph.attach(self.__spin_morph, 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_morph.attach(self.__combo_contour, 1, 2, 1, 2, gtk.FILL, gtk.SHRINK)
        #Pack signal
        self.__table_signal.attach(self.__label_order, 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_signal.attach(self.__label_freq, 1, 2, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_signal.attach(self.__label_minim, 2, 3, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_signal.attach(self.__spin_order, 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_signal.attach(self.__range_freq, 1, 2, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_signal.attach(self.__spin_minim, 2, 3, 1, 2, gtk.FILL, gtk.SHRINK)
        #Pack in their respective self.__frame_
        self.__frame__filter.add(self.__table_filter)
        self.__frame__morph.add(self.__table_morph)
        self.__frame__signal.add(self.__table_signal)
        #Pack in main table
        self.__table_configSelection.attach(self.__frame__filter, 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        self.__table_configSelection.attach(self.__frame__morph, 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        self.__table_configSelection.attach(self.__frame__signal, 0, 1, 2, 3, gtk.FILL, gtk.SHRINK)
        self.__table_configSelection.attach(button_restore, 0, 1, 3, 4, gtk.FILL, gtk.SHRINK)
        #Config tables
        self.__table_configSelection.set_border_width(5)
        self.__table_configSelection.set_row_spacings(10)
        self.__table_filter.set_border_width(5)
        self.__table_morph.set_border_width(5)
        self.__table_signal.set_border_width(5)
        'Connect signals'
        button_restore.connect("clicked", self.__on_config_change, 0)
        self.__spin_blur.connect("value_changed", self.__on_config_change, 1)
        self.__range_sigma.connect("value_changed", self.__on_config_change, 2)
        self.__combo_type.connect("changed", self.__on_config_change, 3)
        self.__spin_morph.connect("value_changed", self.__on_config_change, 4)
        self.__combo_contour.connect("changed", self.__on_config_change, 5)
        self.__spin_order.connect("value_changed", self.__on_config_change, 6)
        self.__range_freq.connect("value_changed", self.__on_config_change, 7)
        self.__spin_minim.connect("value_changed", self.__on_config_change, 8)
        'Show'
        self.__alignment_regionSelection = gtk.Alignment(0.5, 0.5)
        self.__alignment_regionSelection.add(self.__table_regionSelection)
        self.event_rubberArea = rubber_Area(control_pipe, sending_pipe)
        self.main_widget = gtk.Table(2, 2, False)
        self.main_widget.attach(self.event_rubberArea.main_widget, 0, 1, 0, 2, gtk.SHRINK, gtk.SHRINK)
        self.main_widget.attach(self.__alignment_regionSelection, 1, 2, 0, 1)
        self.main_widget.attach(self.__table_configSelection, 1, 2, 1, 2)
        self.main_widget.show_all()
        #Config elements
        self.__set_combos()
        'Connect signals'
        for button in self.__buttons_region:
            button.connect("toggled", self.__on_toggle)
        'Show'
        return   
     
    def __call__(self, cam_clicked):
        if self.event_rubberArea.can_draw() != self.__request_draw[0]:
            self.event_rubberArea.set_event_area_sensitive(self.__request_draw[0], self.__request_draw[1])
        active = [False] * 6
        for i in xrange(3):
            active[i] = self.__buttons_region[i].get_active()
            active[i+3] = self.__checks_region[i].get_active()
            self.__set_icon(i, type(self.event_rubberArea.get_ROI()[i]) != NoneType)  
        self.event_rubberArea(self.__actual_config, active, cam_clicked)
        if self.event_rubberArea.return_state[0]:
            self.__buttons_region[self.event_rubberArea.return_state[1]].set_active(False)
            self.event_rubberArea.return_state[0] = False
        return
    
    def __set_defaults(self):
        def_ = self.__file_default.read('list', 'cameras', 'config')
        lim_ = self.__file_default.read('list', 'adjustments', 'limits')
        inc_ = self.__file_default.read('list', 'adjustments', 'increments')
        'Set adjustments from default configuration'
        self.__adjustment_ker = gtk.Adjustment(def_[0], lim_[0][0], lim_[0][1], inc_[0], inc_[0], 0)
        self.__adjustment_sig = gtk.Adjustment(def_[1], lim_[1][0], lim_[1][1], inc_[1], inc_[1], 0)
        self.__adjustment_mor = gtk.Adjustment(def_[3], lim_[2][0], lim_[2][1], inc_[2], inc_[2], 0) 
        self.__adjustment_ord = gtk.Adjustment(def_[5], lim_[3][0], lim_[3][1], inc_[3], inc_[3], 0)
        self.__adjustment_fre = gtk.Adjustment(def_[6], lim_[4][0], lim_[4][1], inc_[4], inc_[4], 0)
        self.__adjustment_min = gtk.Adjustment(def_[7], lim_[5][0], lim_[5][1], inc_[5], inc_[5], 0)
        self.__actual_config = def_ 
        return
    
    def __on_config_change(self, widget, data = None):
        if data == 0:
            def_ = self.__file_default.read('list', 'cameras', 'config')
            self.__adjustment_ker.set_value(def_[0])
            self.__adjustment_sig.set_value(def_[1])
            self.__combo_type.set_active(def_[2])
            self.__adjustment_mor.set_value(def_[3]) 
            self.__combo_contour.set_active(def_[4])
            self.__adjustment_ord.set_value(def_[5]) 
            self.__adjustment_fre.set_value(def_[6]) 
            self.__adjustment_min.set_value(def_[7])
            self.__actual_config = def_
            self.__update = [True, True, True]
            for check in self.__checks_region:
                check.set_active(False)
            return
        elif data == 1:
            temp = self.__spin_blur.get_value_as_int()
        elif data == 2:
            temp = int(self.__range_sigma.get_value())
        elif data == 3:
            temp = self.__combo_type.get_active()
        elif data == 4:
            temp = self.__spin_morph.get_value_as_int()
        elif data == 5:
            temp = self.__combo_contour.get_active()
        elif data == 6:
            temp = self.__spin_order.get_value_as_int()
        elif data == 7:
            temp = self.__range_freq.get_value()
        elif data == 8:
            temp = self.__spin_minim.get_value_as_int()
        self.__update = [(data < 4), ((data < 6) & (data >= 4)), (data >= 6)]
        self.__actual_config[data-1] = temp
        return

    def __set_combos(self):
        strings = self.__file_default.read('str', 'combos', 'filter')
        for string in strings:
            self.__combo_type.append_text(string)
        self.__combo_type.set_active(0)
        strings = self.__file_default.read('str', 'combos', 'contour')
        for string in strings:
            self.__combo_contour.append_text(string)
        self.__combo_contour.set_active(0)
        return
    
    def __set_icon(self, region, status):
        modes = (gtk.STOCK_CANCEL, gtk.STOCK_APPLY)
        if region == 'all':
            for index in xrange(3):
                self.__icons_region[index].set_from_stock(modes[status], gtk.ICON_SIZE_BUTTON)
        else:
            self.__icons_region[region].set_from_stock(modes[status], gtk.ICON_SIZE_BUTTON)
        return      
     
    def __on_toggle(self, widget):
        temp = self.__buttons_region[self.__buttons_region.index(widget)].get_active()
        self.__request_draw = [temp, self.__buttons_region.index(widget)]
        self.__buttons_region[self.__buttons_region.index(widget)-1].set_sensitive(not temp)
        self.__buttons_region[self.__buttons_region.index(widget)-2].set_sensitive(not temp)
        return
    
    def get_config(self):
        return self.__actual_config
    
    def get_color(self):
        return self.event_rubberArea.get_color()
     
    def reset(self):
        self.__on_config_change(None, 0)
        for check, button in zip(self.__checks_region, self.__buttons_region):
            check.set_active(False)
            button.set_active(False)
        self.__request_draw = [False, 0]
        self.__set_icon('all', False)
        self.event_rubberArea.reset()
        return
     
    def update(self, region):
        self.__region_buttons[region].set_active(False)
        self.__set_icon(region, True)
        return
    
   
    
class rubber_Area(object):
    def __init__(self, control_pipe, sending_pipe, resolution = [640, 480]):
        self.__control_pipe = control_pipe
        self.__sending_pipe = sending_pipe
        self.__resolution = resolution
        self.return_state = [False, 0]
        self.__color = [None] * 9
        self.__image = gtk.Image()
        #self.__frame.set_border_width(10)
        self.__cursor = gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)  
        self.main_widget = gtk.EventBox()
        self.main_widget.set_size_request(self.__resolution[0], self.__resolution[1])
        self.main_widget.add(self.__image)
        self.__id_init = self.main_widget.connect("button_press_event", self.__rubber_band)
        self.__id_drag = self.main_widget.connect("motion_notify_event", self.__rubber_band)
        self.__id_end = self.main_widget.connect("button_release_event", self.__rubber_band)
        self.reset()
        self.set_event_area_sensitive(False)
        return
     
    def __call__(self, config, active_toogles = None, cam_clicked = None):
        '''
        set the image on the event area depending on the mode:
            align: draw a vertical and an horizontal line in the center of the image 
            rubber: draw rectangles in the selected region of interest
        '''
        self.__cam_clicked = cam_clicked
        self.__actual_config = config
        if self.__sending_pipe.poll():
            self.__imageRGB = self.__sending_pipe.recv()[cam_clicked]
            self.__control_pipe.send(True)
        else:
            return
        d = 0
        for i in self.__ROI:
            if type(i) != NoneType:
                d += 1
            if d == 3:
                self.__get_filter()
                self.__get_segment()
        try:
            dummy = active_toogles[3:6].index(True)
            results = self.__segment(self.__filter(cvtColor(self.__imageRGB, CV_RGB2HSV)))
            self.__imageRGB = masked_image(self.__imageRGB, results[1], active_toogles[3:6]).image
        except:
            pass
        try:
            dummy = active_toogles[0:3].index(True)
            mode = 'rubber'
        except:
            mode = 'align'  
        pixbuf = gtk.gdk.pixbuf_new_from_array(self.__imageRGB, gtk.gdk.COLORSPACE_RGB, 8)
        self.__pixmap, self.__mask = pixbuf.render_pixmap_and_mask()
        try:
            self.__cmap = self.__cmap
        except:
            self.__cmap = self.__pixmap.get_colormap()
            self.__cmap_rgb=[]
            self.__cmap_rgb.append(self.__pixmap.new_gc(self.__cmap.alloc_color('red')))
            self.__cmap_rgb.append(self.__pixmap.new_gc(self.__cmap.alloc_color('green')))
            self.__cmap_rgb.append(self.__pixmap.new_gc(self.__cmap.alloc_color('blue')))
        if mode == 'align':
            self.__pixmap.draw_line(self.__cmap_rgb[0], 0, self.__resolution[1]/2, self.__resolution[0], self.__resolution[1]/2)
            self.__pixmap.draw_line(self.__cmap_rgb[0], self.__resolution[0]/2, 0, self.__resolution[0]/2, self.__resolution[1])   
        elif mode == 'rubber':
            for index in xrange(3):
                if type(self.__coordinates_xy[index]) != NoneType:
                    coord = self.__coordinates_xy[index]
                    color = self.__cmap_rgb[index]
                    size = diff(coord)
                    self.__pixmap.draw_rectangle(color, False, coord[0][0], coord[1][0], size[0], size[1])
        self.__image.set_from_pixmap(self.__pixmap, self.__mask)
        return
         
    def __rubber_band(self, widget, event, data = None):
        #set delimiters, if the event occur outside the image
        event.x = 0.0 if event.x < 0 else event.x
        event.x = float(self.__resolution[0]) if event.x > self.__resolution[0] else event.x
        event.y = 0.0 if event.y < 0 else event.y
        event.y = float(self.__resolution[1]) if event.y > self.__resolution[1] else event.y
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.__rubber_xy[0][0] = event.x
            self.__rubber_xy[1][0] = event.y
            return
        else:
            self.__rubber_xy[0][1] = event.x
            self.__rubber_xy[1][1] = event.y
            coord = array([sorted(self.__rubber_xy[0]), sorted(self.__rubber_xy[1])]).astype(int)
            if event.type == gtk.gdk.BUTTON_RELEASE:
                self.__get_ROI(coord)
                self.__get_threshold()
                self.__rubber_xy = [[0, 1], [1, 1]]
                self.return_state = [True, self.__area]
        self.__coordinates_xy[self.__area] = coord     
        return
    
    def __get_ROI(self,coord):
        subregion = zeros(((coord[1][1] - coord[1][0]), (coord[0][1] - coord[0][0]), 3), uint8)
        subregion[:,:,:] = self.__imageRGB[coord[1][0] : coord[1][1], coord[0][0] : coord[0][1], :]
        self.__ROI[self.__area] = cvtColor(subregion, CV_RGB2HSV)
        return
    
    def __get_threshold(self):
        try:
            for thresh in self.__thresholders:
                thresh.update_config(self.__actual_config[5:8])
        except:
            self.__thresholders =[thresholder(self.__actual_config[5:8])] * 3
        self.__thresholders[self.__area](self.__ROI[self.__area])
        self.__color[(self.__area*3)] = self.__thresholders[self.__area].CTR
        self.__color[(self.__area*3)+1] = self.__thresholders[self.__area].MIN
        self.__color[(self.__area*3)+2] = self.__thresholders[self.__area].MAX
        return
    
    def __get_filter(self):
        try:
            self.__filter.update_config(self.__actual_config[0:3])
        except:
            self.__filter = filter_pool(self.__actual_config[0:3])
        return
    
    def __get_segment(self):
        try:
            self.__segment.update_config(self.__actual_config[3:5], self.__color)
        except:
            self.__segment = segment_pool(self.__actual_config[3:5], self.__color)
        return
         
    def set_event_area_sensitive(self, mode, area = None):
        self.__area = area if area != None else self.__area
        self.__can_draw = mode
        if mode:
            self.main_widget.handler_unblock(self.__id_init)
            self.main_widget.handler_unblock(self.__id_drag)
            self.main_widget.handler_unblock(self.__id_end)
            if self.main_widget.window != None:
                self.main_widget.window.set_cursor(self.__cursor)
        else:
            self.main_widget.handler_block(self.__id_init)
            self.main_widget.handler_block(self.__id_drag)
            self.main_widget.handler_block(self.__id_end)
            if self.main_widget.window != None:
                self.main_widget.window.set_cursor(None)
        return
    
    def reset(self):
        self.__rubber_xy = [[0, 1], [1, 1]]
        self.__coordinates_xy = [None] * 3
        self.__ROI = [None] * 3
        self.__area = 0
        return
     
    def can_draw(self):
        return self.__can_draw
    
    def get_ROI(self):
        return self.__ROI
    
    def get_color(self):
        return self.__color


class plot_data(object):
    '''
    Creates a object with a widget ready to be inserted in a GTK window, in wich we can 
    plot the current robot variables.
                    
    calling the object will update the plot with the data passed
    calling the method set_values you can change the color, units a/o length
    '''
    def __init__(self, units=None, colors=None, length=None):
        '''
         Modifiable attributes:
         colors: color of the lines - list of strings: len = 4 default: ['r', 'g', 'b', 'y']
         units: units of the plots - list of strings: len = 2 default: [rad, N*m]
         length: maximum period of time to show - int or float default: 100
        
         Accessible attributes:
         main_widget: widget to be inserted in a GTK window
        '''
        self.set_values(units, colors, length)
        # Define axis and lines labels
        self.__xlabel = 'Time - s'
        self.__ylabel = ['Angular position - '+self.__units[0], 'Angular velocity - '+self.__units[0]+'/s', 
                         'Angular acceleration - '+self.__units[0]+'/s**2', 'Torque - '+self.__units[1]]
        self.__lines_labels = ["Shoulder_X", "Shoulder_Y", "Shoulder_Z", "Elbow_Z"]
        # Define font size for the legend
        self.__font = font_manager.FontProperties(size = 8)
        # Create the Figure and the plot
        self.__figure = figure()
        self.__sub_figures = []
        self.__backgrounds = []
        self.__lines = [[], [], [], []]
        # Create the widget, a FigureCanvas containing our Figure
        self.main_widget = FigureCanvas(self.__figure)
        # Create and configure the subplots
        for index in xrange(4):
            self.__sub_figures.append(self.__figure.add_subplot(221+index))
            self.__sub_figures[index].grid(True)
            self.__sub_figures[index].set_xlabel(self.__xlabel, fontsize = 9)
            self.__sub_figures[index].set_ylabel(self.__ylabel[index], fontsize = 9)
            #FIXME: change the y limits, the currents are for test only
            self.__sub_figures[index].set_ylim(-256, 256)
            self.__sub_figures[index].set_xlim(0, self.__lenght)
            self.__sub_figures[index].tick_params(axis='both', which = 'major', labelsize = 10)
            self.__sub_figures[index].tick_params(axis='both', which = 'minor', labelsize = 8)
            for l_index in xrange(4):
                self.__lines[index].append(self.__sub_figures[index].plot([], [], self.__colors[l_index], animated = True)[0])
            #Saving the firsts background to redraw 
            self.__backgrounds.append(self.main_widget.copy_from_bbox(self.__sub_figures[index].bbox))
        #Setting up the legend box
        figlegend(self.__lines[0], self.__lines_labels, loc = "upper center", prop= self.__font)
        #Show and set initial data
        self.main_widget.draw()
        self.__reset_data()
        return
        
    def __call__(self, values, d_time):
        '''
        values: object with the current values to plot, in the form of attributes like:
            self.position = []
            self.velocity = []
            self.acceleration = []
            self.torque = []
        
        d_time: current time, since the plot starts - int or float
        '''
        self.__time.append(d_time)
        if (d_time >= (self.__time[0] + self.__lenght)):
            self.__reset_data()
            self.__time.append(d_time)
            for index in xrange(4):
                self.__sub_figures[index].set_xlim(d_time, d_time+self.__lenght)
            self.main_widget.draw()
            for index in xrange(4):
                self.__backgrounds[index] = self.main_widget.copy_from_bbox(self.__sub_figures[index].bbox)
        for index in xrange(4):
            self.main_widget.restore_region(self.__backgrounds[index])
            self.__position[index].append(values.position[index])
            self.__velocity[index].append(values.velocity[index])
            self.__acceleration[index].append(values.acceleration[index])
            self.__torque[index].append(values.torque[index])
        for index in xrange(4):
            for l_index in xrange(4):
                if index == 0:
                    self.__lines[index][l_index].set_data(self.__time, self.__position[l_index])
                elif index == 1:
                    self.__lines[index][l_index].set_data(self.__time, self.__velocity[l_index])
                elif index == 2:
                    self.__lines[index][l_index].set_data(self.__time, self.__acceleration[l_index])
                elif index == 3:
                    self.__lines[index][l_index].set_data(self.__time, self.__torque[l_index])
                self.__sub_figures[index].draw_artist(self.__lines[index][l_index])
            self.main_widget.blit(self.__sub_figures[index].bbox)
        return
        
    def __reset_data(self):
        #Create the vectors for the variables
        try: 
            type(self.__time)
        except:
            self.__time = []
            self.__position = [[], [], [], []]
            self.__velocity = [[], [], [], []]
            self.__acceleration = [[], [], [], []]
            self.__torque = [[], [], [], []]
            return
        #If the vectors are already created, then only leave the last value
        del(self.__time[-2:0:-1])
        self.__time.pop(0)
        for index in xrange(4):
            del(self.__position[index][-2:0:-1])
            del(self.__velocity[index][-2:0:-1])
            del(self.__acceleration[index][-2:0:-1])
            del(self.__torque[index][-2:0:-1])
            self.__position[index].pop(0)
            self.__velocity[index].pop(0)
            self.__acceleration[index].pop(0)
            self.__torque[index].pop(0)
        return
    
    def set_values(self, units=None, colors=None, length=None):
        self.__units = ["rad", "N*m"] if type(units) is NoneType else units
        self.__colors = ['r', 'g', 'b', 'y'] if type(colors) is NoneType else colors
        self.__lenght = 100 if type(length) is NoneType else length
        return


class animate_data(object):
    '''
    Creates a object with a widget ready to be inserted in a GTK window, in wich we can 
    draw the current robot pose.
                    
    calling the object will draw the robot pose with the data passed
    calling the method zoom(in,out,reset) will change the zoom of the scene
    calling the method rotate(left,right,reset) will rotate the model along the vertical 
        axe of the scene
    calling the method can_zoom will return the available zoom actions
        -1 zoom out, 0 all, 1 zoom in
    calling the method can_animate return if the animation is available
        bool
    '''
    def __init__(self, user_height = None):
        '''
         Modifiable attributes:
         user_height: as sounds - int default: 180 (centimeters)
        
         Accessible attributes:
         main_widget: widget to be inserted in a GTK window
        '''
        # initialize values
        self.__user_height = 180 if user_height == None else user_height
        self.__upper_arm = self.__user_height * 0.0188
        self.__forearm = self.__user_height * 0.0145
        self.__initial_distance = 20
        self.__initial_angle = 0
        self.__minimum_distance = 10
        self.__maximum_distance = 30
        self.__can_zoom = 0
        self.__can_animate = True
        self.__distance = self.__initial_distance
        self.__angle = self.__initial_angle
        self.__distance_delta = 1.0
        self.__angle_delta = 5.0 * pi /180
        #SHOULDER_X, SHOULDER_Y, SHOULDER_Z, ELBOW_Z
        self.__arm_angles = [0, 0, 0, 0]
        # Try to create a double buffered framebuffer,
        # if not successful then try to create a single
        # buffered one.
        self.__display_mode = MODE_RGB | MODE_DEPTH | MODE_DOUBLE
        try:
            self.__glconfig = Config(mode=self.__display_mode)
        except NoMatches:
            self.__display_mode &= ~MODE_DOUBLE
            self.__glconfig = Config(mode=self.__display_mode)
        # DrawingArea for OpenGL rendering.
        self.__glarea = DrawingArea(self.__glconfig)
        self.__glarea.set_size_request(400, 400)
        self.__label = gtk.Label("Deactivate Animation/Simulation") 
        # The toggle button itself.
        self.main_widget = gtk.ToggleButton()
        # A VBox to pack the glarea and label.
        vbox = gtk.VBox()
        vbox.set_border_width(10)
        vbox.pack_start(self.__glarea)
        vbox.pack_start(self.__label, False, False, 10)
        self.main_widget.add(vbox)
        # connect to the relevant signals.
        self.__glarea.connect_after('realize', self.__update)
        self.__glarea.connect('configure_event', self.__resize)
        self.__glarea.connect('expose_event', self.__draw)
        self.main_widget.connect('toggled', self.__toggle)        
        self.main_widget.show_all()
        return
        
    def __call__(self, values):
        '''
        values: object with the current angles values to draw, in the form of list
        '''
        if not self.__can_animate:
            return
        for index in xrange(4):
            self.__arm_angles[index] = values[index]
        self.__redraw()
        return
    
    def __update(self, widget):
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        # OpenGL begin.
        if not gldrawable.gl_begin(glcontext):
            return
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)    # The type of depth test to do
        glEnable(GL_DEPTH_TEST | GL_LINE_SMOOTH) # Turn on depth testing.
        gldrawable.gl_end()
        # OpenGL end
        return
    
    def __resize(self, widget, event):
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        # OpenGL begin.
        if not gldrawable.gl_begin(glcontext):
            return
        width = widget.allocation.width
        height = widget.allocation.height
        glViewport (0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, 1.0, -1.0, 1.0, 1.5, 300.0)
        glMatrixMode (GL_MODELVIEW)
        gldrawable.gl_end()
        # OpenGL end
        return

    def __draw(self, widget, event):
        x = self.__distance * sin(self.__angle)
        z = self.__distance * cos(self.__angle)
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        # OpenGL begin.
        if not gldrawable.gl_begin(glcontext):
            return
        glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity ()
        gluLookAt(x, 0.0, z, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)  
        #==========================
        glPushMatrix()
        glLineWidth(3)
        glRotatef(self.__arm_angles[0], 1., 0., 0.)
        glRotatef(self.__arm_angles[1], 0., 1., 0.)
        glRotatef(self.__arm_angles[2], 0., 0., 1.)
        glTranslatef(self.__upper_arm, 0., 0.)
        #==========================
        glPushMatrix()
        glColor3f(30./255., 126./255., 30./255.)
        glScalef(self.__upper_arm, 0.4, 1.0)
        self.__draw_cube()       # shoulder
        glPopMatrix()
        #==========================
        glTranslatef(self.__upper_arm, 0., 0.)
        glRotatef(self.__arm_angles[3] , 0., 0., 1.)
        glTranslatef(self.__forearm, 0., 0.)
        glPushMatrix()
        #==========================
        glScalef(self.__forearm, 0.3, 0.75)
        glColor3f(126./255., 30./255., 30./255.)
        self.__draw_cube()      # elbow
        glPopMatrix()
        glPopMatrix()
        #==========================
        if gldrawable.is_double_buffered():
            gldrawable.swap_buffers()
        else:
            glFlush()
        gldrawable.gl_end()
        # OpenGL end
        return

    def __redraw(self):
        self.__glarea.queue_draw()
        return

    def __toggle(self, widget):
        self.__can_animate = not self.main_widget.get_active()
        if self.__can_animate:
            self.__label.set_label("Deactivate Animation/Simulation")
        else:
            self.__label.set_label("Activate Animation/Simulation")
        return

    def __draw_cube(self, size = None):
        size = 1 if size == None else size
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        glBegin(GL_QUADS)
        #==========================
        glVertex3f(size,size,size)
        glVertex3f(-size,size,size)
        glVertex3f(-size,-size,size)
        glVertex3f(size,-size,size)
        #==========================
        glVertex3f(size,size,-size)
        glVertex3f(-size,size,-size)
        glVertex3f(-size,-size,-size)
        glVertex3f(size,-size,-size)
        #==========================
        glVertex3f(size,size,size)
        glVertex3f(size,-size,size)
        glVertex3f(size,-size,-size)
        glVertex3f(size,size,-size)
        #==========================
        glVertex3f(-size,size,size)
        glVertex3f(-size,-size,size)
        glVertex3f(-size,-size,-size)
        glVertex3f(-size,size,-size)
        #==========================
        glVertex3f(size,size,size)
        glVertex3f(-size,size,size)
        glVertex3f(-size,size,-size)
        glVertex3f(size,size,-size)
        #==========================
        glVertex3f(size,-size,size)
        glVertex3f(-size,-size,size)
        glVertex3f(-size,-size,-size)
        glVertex3f(size,-size,-size)
        #==========================
        glEnd()
        return
    
    def zoom(self, in_out = None):
        # in_out values: -1 zoom out, 0 reset view, 1 zoom in
        if ((in_out == -1) | (in_out == 'out')) & (self.__can_zoom != 1):
            self.__distance += self.__distance_delta
            self.__can_zoom = 1 if self.__distance >= self.__maximum_distance else 0
        elif (in_out == 0) | (in_out == 'reset'):
            self.__distance = self.__initial_distance
            self.__can_zoom = 0
        elif ((in_out == 1) | (in_out == 'in')) & (self.__can_zoom != -1):
            self.__distance -= self.__distance_delta
            self.__can_zoom = -1 if self.__distance <= self.__minimum_distance else 0 
        self.__redraw()
        return
    
    def can_zoom(self):
        return self.__can_zoom
    
    def rotate(self, direction = None):
        # direction values: -1 rotate left, 0 reset view, 1 rotate right
        if (direction == -1) | (direction == 'left'):
            self.__angle -= self.__angle_delta
        elif (direction == 0) | (direction == 'reset'):
            self.__angle = self.__initial_angle
        elif ((direction == 1) | (direction == 'right')):
            self.__angle += self.__angle_delta
        self.__redraw()
        return
    
    def can_animate(self):
        return self.__can_animate

    
class binary_images(object):
    def __init__(self, resolution, cameras_names):
        self.__resolution = resolution
        cameras= cameras_names
        labels = map(gtk.Label, [i_ + " camera" for i_ in cameras])
        self.__images = [gtk.Image() for i_ in cameras]
        self.__none_mask = zeros((self.__resolution[1], self.__resolution[0]), uint8)
        for i_ in self.__images:
            i_.set_size_request(self.__resolution[0]/2, self.__resolution[1]/2)
            i_.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_LARGE_TOOLBAR)
         
        self.main_widget = gtk.Frame("Binary images")
        self.__button = gtk.ToggleButton()
        self.__label = gtk.Label("")
         
         
        table = gtk.Table(6, 3, False)
        table.set_row_spacing(5, 10)
        table.set_col_spacing(1, 10)
        table.set_border_width(10)
        table.attach(labels[0], 0, 1, 0, 1, gtk.FILL, gtk.SHRINK)
        table.attach(self.__images[0], 0, 1, 1, 2, gtk.FILL, gtk.SHRINK)
        table.attach(labels[1], 2, 3, 0, 1, gtk.FILL, gtk.SHRINK)
        table.attach(self.__images[1], 2, 3, 1, 2, gtk.FILL, gtk.SHRINK)
        table.attach(labels[2], 0, 1, 3, 4, gtk.FILL, gtk.SHRINK)
        table.attach(self.__images[2], 0, 1, 4, 5, gtk.FILL, gtk.SHRINK)
        table.attach(self.__label, 0, 3, 5, 6 , gtk.FILL, gtk.SHRINK)
         
        self.__button.add(table)
        self.main_widget.add(self.__button)
        self.main_widget.show_all()
        self.__button.connect('toggled', self.__on_toggle)
        self.__on_toggle(None)
        return
     
    def __call__(self, filled):
        for i_ in range(3):
            for j_ in range(3):
                if type(filled[i_][j_]) == NoneType:
                    filled[i_][j_] = self.__none_mask
            image = resize(merge((filled[i_][0], filled[i_][1], filled[i_][2])), (self.__resolution[0]/2, self.__resolution[1]/2))        
            self.__images[i_].set_from_pixbuf(gtk.gdk.pixbuf_new_from_array(image, gtk.gdk.COLORSPACE_RGB, 8))
        return
     
    def __on_toggle(self, widget):
        labels = ('Deactivate ', 'Activate ')
        self.__label.set_label(labels[self.__button.get_active()] + "binary stream")
        if self.__button.get_active():
            for i_ in self.__images:
                i_.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_LARGE_TOOLBAR)
        return
     
    def can_draw(self):
        return not self.__button.get_active()       