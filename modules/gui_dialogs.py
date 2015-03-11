#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk, __builtin__
from os import popen, listdir
from gui_widgets import plot_data, animate_data
from shutil import copyfile
from api_files import config_file
from types import NoneType


class splash():     
    def __init__(self):
        #Variable define 
        spl_img_path = __builtin__.MEDIA_PATH + "/splash.png"
        #Gui construction    
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_position(gtk.WIN_POS_CENTER)
        self.win.set_decorated(False)
        
        main_vbox = gtk.VBox(False, 1)
        ver_hbox = gtk.HBox(True, 1)
        lic_hbox = gtk.HBox(True, 1)
        image = gtk.Image()
        lbl_ver = gtk.Label("Version: ")
        lbl_ver_str = gtk.Label(__builtin__.METADATA.find("./version").text)
        lbl_lic = gtk.Label("License: ")
        lbl_lic_str = gtk.Label(__builtin__.METADATA.find("./license").text)
        self.prog = gtk.ProgressBar()  
        
        #Packaging          
        self.win.add(main_vbox)
        main_vbox.pack_start(image, True, True)  
        main_vbox.pack_start(ver_hbox,True, True)
        main_vbox.pack_start(lic_hbox,True, True)
        ver_hbox.pack_start(lbl_ver, False, False)
        ver_hbox.pack_start(lbl_ver_str, False, False)
        lic_hbox.pack_start(lbl_lic, False, False)
        lic_hbox.pack_start(lbl_lic_str, False, False)
        main_vbox.pack_start(self.prog, True, True)
        
        #Configuration
        image.set_from_file(spl_img_path)
        self.prog.set_pulse_step(.25)
        
        #Show
        self.win.show_all()
        while gtk.events_pending():
            gtk.main_iteration()
            
    def destroy(self):
        self.win.destroy()
        
    def update(self):
        self.prog.pulse()


class simulation(gtk.Window):
    def __init__(self, parent = None, user_height = None, units = None, colors = None):
        gtk.Window.__init__(self)
        self.__step = 0
        self.__is_hide = False
        self.__screen = [0, 0]
        self.__screen[0] = int(popen("xrandr -q -d :0").readlines()[0].split()[7])
        self.__screen[1] = int(popen("xrandr -q -d :0").readlines()[0].split()[9][:-1])
        self.__controls()
        self.__plotter = plot_data(units, colors, int(self.__range_period.get_value()))
        div = {'mm': 10, 'cm': 1, 'm':.01}
        self.__animator = animate_data(user_height/div[units[0]])
        self.__plotter.main_widget.set_size_request(int(0.62*self.__screen[0]), int(0.78*self.__screen[1]))
        self.__animator.main_widget.set_size_request(int(0.39*self.__screen[1]), int(0.48*self.__screen[1]))
        self.__controls_frame.set_size_request(int(0.39*self.__screen[1]), int(0.3*self.__screen[1]))
        
        self.__main_table = gtk.Table(2, 2, False)
        self.__main_table.attach(self.__plotter.main_widget, 0, 1, 0, 2, gtk.SHRINK, gtk.SHRINK)
        self.__main_table.attach(self.__animator.main_widget, 1, 2, 0, 1, gtk.SHRINK, gtk.SHRINK)       
        self.__main_table.attach(self.__controls_frame, 1, 2, 1, 2, gtk.SHRINK, gtk.SHRINK)
        
        self.main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.main_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.main_window.add(self.__main_table)
        self.main_window.set_title("Animation and Simulation")
        self.main_window.set_resizable(False)
        self.main_window .show_all()
        self.main_window.connect('delete-event', self.__do_nothing)
        
        
    
    def __call__(self, value, d_time):
        self.__step += 1
        if (self.__step >= self.__range_step.get_value()) & self.__animator.can_animate() & (not self.__is_hide):
            self.__plotter(value, d_time)
            self.__animator(value.position)
            self.__step = 0
        return
        
    def __controls(self):
        self.__adj_period = gtk.Adjustment(5, 1, 21, 1, 1, 1)
        self.__adj_step = gtk.Adjustment(2, 1, 21, 1, 1, 1)
        
        self.__button_rotate_left = gtk.Button()
        self.__button_rotate_right = gtk.Button()
        self.__button_zoom_in = gtk.Button()
        self.__button_zoom_out = gtk.Button()
        self.__button_rotate_left.set_image(self.__set_icon(1))
        self.__button_rotate_right.set_image(self.__set_icon(0))
        self.__button_zoom_in.set_image(self.__set_icon(2))
        self.__button_zoom_out.set_image(self.__set_icon(3))
        self.__button_reset_view = gtk.Button('Reset')
        self.__range_period = gtk.HScale(self.__adj_period)
        self.__range_period.set_size_request(int(0.117*self.__screen[0]), 50)
        self.__range_period.set_digits(0)
        self.__range_step = gtk.HScale(self.__adj_step)
        self.__range_step.set_size_request(int(0.117*self.__screen[0]), 50)
        self.__range_step.set_digits(0)
        
        self.__button_rotate_left.connect('clicked', self.__click_button, 'left')
        self.__button_rotate_right.connect('clicked', self.__click_button, 'right')
        self.__button_zoom_in.connect('clicked', self.__click_button, 'in')
        self.__button_zoom_out.connect('clicked', self.__click_button, 'out')
        self.__button_reset_view.connect('clicked', self.__click_button, 'reset')
        self.__range_period.connect('value_changed', self.__period_change)
        
        table = gtk.Table(6,5,False)
        table.set_row_spacings(5)
        table.set_border_width(10)
        table.attach(self.__range_period, 0, 2, 0, 1, gtk.EXPAND, gtk.SHRINK)
        table.attach(self.__range_step, 3, 5, 0, 1, gtk.EXPAND, gtk.SHRINK)
        table.attach(gtk.Label('Plot period - s'), 0, 2, 1, 2, gtk.SHRINK, gtk.SHRINK)
        table.attach(gtk.Label('Step'), 3, 5, 1, 2, gtk.SHRINK, gtk.SHRINK)
        table.attach(gtk.HSeparator(), 0, 5, 2, 3, gtk.FILL, gtk.FILL)
        table.attach(self.__button_zoom_in, 2, 3, 3, 4, gtk.SHRINK, gtk.SHRINK)
        table.attach(self.__button_rotate_left, 1, 2, 4, 5, gtk.SHRINK, gtk.SHRINK)
        table.attach(self.__button_reset_view, 2, 3, 4, 5, gtk.SHRINK, gtk.FILL)
        table.attach(self.__button_rotate_right, 3, 4, 4, 5, gtk.SHRINK, gtk.SHRINK)
        table.attach(self.__button_zoom_out, 2, 3, 5, 6, gtk.SHRINK, gtk.SHRINK)
        
        self.__controls_frame = gtk.Frame('Animation/simulation controls')
        self.__controls_frame.set_label_align(1.0, 0.5)
        self.__controls_frame.set_border_width(10)
        self.__controls_frame.add(table)
        return
    
    def __do_nothing(self, widget, event):
        return True
  
    def __set_icon(self, icon):
        icons = ["STOCK_REDO", "STOCK_UNDO", "STOCK_ZOOM_IN", "STOCK_ZOOM_OUT"]
        image = gtk.Image()
        image.set_from_stock(eval("gtk."+icons[icon]), gtk.ICON_SIZE_LARGE_TOOLBAR)
        return image
    
    def __click_button(self, widget, data = None):
        if (data == "left") | (data == "right"):
            self.__animator.rotate(data)
        elif (data == "in") | (data == "out") | (data == "reset"):
            self.__animator.zoom(data)   
            self.__button_zoom_in.set_sensitive(self.__animator.can_zoom()!=-1)
            self.__button_zoom_out.set_sensitive(self.__animator.can_zoom()!=1)
        return
    
    def __period_change(self, widget, data = None):
        self.__plotter.set_values(length = int(self.__range_period.get_value()))
        return
    
    def set_visible(self, widget = None, event = None, data = False):
        self.__is_hide = not data
        if data:
            self.main_window.show()
            self.main_window.set_focus_on_map(False)
        else:
            self.main_window.hide()
        return True
    
    def get_visible(self):
        return not self.__is_hide
    
    def destroy_window(self, widget = None):
        self.main_window.destroy()
        return

        
def create_project():
    dialog = gtk.FileChooserDialog("Create new project...", None, gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_modal(True)
    filter_ = gtk.FileFilter()
    filter_.set_name("All files")
    filter_.add_pattern("*")
    dialog.add_filter(filter_)
    response = None
    while response == None:
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            if dialog.get_current_folder() != None:
                response = dialog.get_filename()
                if len(listdir(dialog.get_filename())) > 0:
                    invalid_folder()
                else:
                    open(response + '/.isHekateProject', 'w')
                    copyfile(__builtin__.MEDIA_PATH+'/project.cfg', response+'/.project.cfg')
                    copyfile(__builtin__.MEDIA_PATH+'/default.cfg', response+'/.default.cfg')
                    break
        elif response == gtk.RESPONSE_CANCEL:
            response = None
            break
        response = None
    dialog.destroy()
    print 'New project at:', response
    return response

    
def select_project():
    dialog = gtk.FileChooserDialog("Select existing project...", None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_modal(True)
    filter_ = gtk.FileFilter()
    filter_.set_name("All files")
    filter_.add_pattern("*")
    dialog.add_filter(filter_)
    response = None
    while response == None:
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            response = dialog.get_filename()
            if ('.isHekateProject' not in listdir(dialog.get_filename())):
                invalid_folder()
            else:
                break
        elif response == gtk.RESPONSE_CANCEL:
            response = None
            break
        response = None
    dialog.destroy()
    print 'Selected project at:', response
    return response


def invalid_folder():
    dialog = gtk.MessageDialog( None, \
                               gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,\
                               gtk.BUTTONS_CLOSE, "Not an empty/valid project folder")
    dialog.set_modal(True)
    dialog.set_keep_above(True)
    dialog.run()
    dialog.destroy()
    return


def about(widget):
    text_file = open(__builtin__.MAIN_PATH + "/COPYING", "r")
    lines = text_file.readlines()
    license_ = ''
    for line in lines:
        license_ += line
    about = gtk.AboutDialog()
    about.set_modal(True)
    about.set_keep_above(True)
    about.set_program_name(__builtin__.METADATA.find("./title").text)
    about.set_version(__builtin__.METADATA.find("./version").text)
    about.set_authors([__builtin__.METADATA.find("./author").text+\
                       ' - <'+__builtin__.METADATA.find("./email").text+'>'])
    about.set_license(license_)
    about.set_copyright(__builtin__.METADATA.find("./copyright").text)
    about.set_comments(__builtin__.METADATA.find("./comment").text)
    about.set_website(__builtin__.METADATA.find("./website").text)
    about.set_logo(gtk.gdk.pixbuf_new_from_file(__builtin__.MEDIA_PATH + "/eye.png"))
    about.run()
    about.destroy()
    return


def default_values(file):
    def on_change(widget, data):
        if data[1] == -1:
            adjMax[data[0]].set_lower(widget.get_value()+inc_[data[0]])
            adjMin[data[0]].set_upper(adjMax[data[0]].get_value()-inc_[data[0]])
            adjDef[data[0]].set_lower(widget.get_value())
            adjDef[data[0]].set_upper(adjMax[data[0]].get_value())
            if adjDef[data[0]].get_value() < widget.get_value():
                adjDef[data[0]].set_value(widget.get_value())
            if adjMax[data[0]].get_value() <= widget.get_value():
                adjMax[data[0]].set_value(widget.get_value()+inc_[data[0]])
        if data[1] == 1:
            adjMin[data[0]].set_upper(widget.get_value()-inc_[data[0]])
            adjMax[data[0]].set_lower(adjMin[data[0]].get_value()+inc_[data[0]])
            adjDef[data[0]].set_upper(widget.get_value())
            adjDef[data[0]].set_lower(adjMin[data[0]].get_value())
            if adjDef[data[0]].get_value() > widget.get_value():
                adjDef[data[0]].set_value(widget.get_value())  
            if adjMin[data[0]].get_value() >= widget.get_value():
                adjMin[data[0]].set_value(widget.get_value()-inc_[data[0]])
        if data[1] == 0:
            adjDef[data[0]].set_upper(adjMax[data[0]].get_value())
            adjDef[data[0]].set_lower(adjMin[data[0]].get_value())
        return
    def OnPlus(widget, data):
        if data:
            boxCameras.remove(boxCameras.get_children()[0])
            boxCameras.pack_start(tableResolutionAdd)
            boxCameras.reorder_child(boxCameras.get_children()[1], 0)
            boxCameras.show_all()
        else:
            boxCameras.remove(boxCameras.get_children()[0])
            boxCameras.pack_start(tableResolution)
            boxCameras.reorder_child(boxCameras.get_children()[1], 0)
            boxCameras.show_all()
            resAdd = [entryWidth.get_text().strip(), entryHeight.get_text().strip()]
            if not ('' in resAdd):
                for i in supported:
                    comboResolution.remove_text(0)
                supported.append([int(val) for val in resAdd])
                supported.sort(reverse = True)
                for res in supported:
                    comboResolution.append_text(str(res)) 
            entryWidth.set_text('')
            entryHeight.set_text('')
            del(i)
        comboResolution.show_all()
        comboResolution.set_active(0) 
        if len(supported) > 1:
            buttonLess.set_sensitive(True)
        return 
    def OnLess(widget):
        supported.pop(comboResolution.get_active())
        comboResolution.remove_text(comboResolution.get_active())
        for i in supported:
            comboResolution.remove_text(0)
            supported.sort(reverse = True)
        for res in supported:
            comboResolution.append_text(str(res))
        comboResolution.show_all()
        comboResolution.set_active(0) 
        if len(supported) < 2:
            buttonLess.set_sensitive(False)
        del(i)
        return
    def OnSelect(widget):
        global select
        select = supported[comboResolution.get_active()]
        return
    def on_entry_res(widget, data):
        if data == 1:
            text = entryHeight.get_text().strip()
            entryHeight.set_text(''.join([i for i in text if i in '0123456789']))
        if data == 0:
            text = entryWidth.get_text().strip()
            entryWidth.set_text(''.join([i for i in text if i in '0123456789']))
        return
    
    def on_entry_remove(widget):
        text = entryRemove.get_text().strip()
        entryRemove.set_text(''.join([i for i in text if i in str(found).replace(',', '').strip('[]')+',']))
        return
    
    def OnAccept(widget, event=None):
        global select
        order = (0, 1, 3, 5, 6, 7)
        config = [5, 50, 0, 3, 0, 3, 0.15, 1]
        string = entryRemove.get_text()
        camLess = (string[0:len(string)]).split(",")
        while '' in camLess:
            camLess.pop(camLess.index(''))
        for cam in camLess:
            if (int(cam) in found) & (len(found) > 3):
                found.pop(found.index(int(cam)))
        for i in xrange(6):
            lim_[i][0] = int(spinMin[i].get_value())
            lim_[i][1] = int(spinMax[i].get_value())
            config[order[i]] = int(spinDef[i].get_value())
            if i == 4:
                config[order[i]] = round(spinDef[i].get_value(), 2)
                lim_[i][0] = round(spinMin[i].get_value(), 2)
                lim_[i][1] = round(spinMax[i].get_value(), 2)
        if not (select in supported):
            select = supported[0]
        default_file.write('as_is', 'cameras', 'supported_resolutions', supported)
        default_file.write('as_is', 'cameras', 'resolution', select)
        default_file.write('as_is', 'cameras', 'numbers', found)
        default_file.write('as_is', 'cameras', 'config', config)
        default_file.write('as_is', 'adjustments', 'limits', lim_)
        return
    global select
    default_file = config_file(file)
    supported = default_file.read('list', 'cameras', 'supported_resolutions')
    select = default_file.read('list', 'cameras', 'resolution')
    found = [0, 1, 2]
    #Element for first panel (supported resolutions)
    frameCams = gtk.Frame('Cameras configuration')
    frameCams.set_border_width(5)
    comboResolution = gtk.combo_box_new_text()
    comboResolution.set_size_request(150, 30)
    for res in supported:
        comboResolution.append_text(str(res))
    comboResolution.set_active(0)
    buttonLess = gtk.Button()
    buttonLess.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
    buttonPlus = gtk.Button()
    buttonPlus.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
    buttonSelect = gtk.Button('Select as default')
    buttonPlus.connect('clicked', OnPlus, True)
    buttonLess.connect('clicked', OnLess)
    buttonSelect.connect('clicked', OnSelect)
    if len(supported) < 2:
        buttonLess.set_sensitive(False)
    #Element for first panel (add resolutions)
    entryWidth = gtk.Entry(max = 4)
    entryHeight = gtk.Entry(max = 4)
    buttonAdd = gtk.Button('Add')
    buttonAdd.connect('clicked', OnPlus, False)
    entryHeight.connect('changed', on_entry_res, 1)
    #Element for first panel (remove cameras from list)
    entryConnected = gtk.Entry(len(str(found)))
    entryConnected.set_text(str(found))
    entryConnected.set_editable(False)
    entryRemove = gtk.Entry(len(str(found))-len(found)-1)
    entryRemove.connect('changed', on_entry_remove)
    #Packing table for adding and removing resolution
    tableResolution = gtk.Table(2, 4, False)
    tableResolution.attach(gtk.Label('Supported resolutions:'), 0, 1, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolution.attach(comboResolution, 1, 2, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolution.attach(buttonLess, 2, 3 , 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolution.attach(buttonPlus, 3, 4, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolution.attach(buttonSelect, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
    tableResolution.set_col_spacings(5)
    tableResolution.set_col_spacing(1, 28)
    #Packing table for adding custom resolution
    tableResolutionAdd = gtk.Table(2, 4, False)
    tableResolutionAdd.attach(entryWidth, 0, 1, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolutionAdd.attach(gtk.Label(' x '), 1, 2, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolutionAdd.attach(entryHeight, 2, 3 , 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolutionAdd.attach(buttonAdd, 3, 4, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableResolutionAdd.attach(gtk.Label('Width'), 0, 1, 1, 2, gtk.FILL, gtk.FILL)
    tableResolutionAdd.attach(gtk.Label('Height'), 2, 3, 1, 2, gtk.FILL, gtk.FILL)
    #Packing table for removing cameras from list
    tableCameras = gtk.Table(2, 3, False)
    tableCameras.attach(gtk.Label('Connected cameras:'), 0, 1, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableCameras.attach(entryConnected, 1, 2, 0, 1, gtk.SHRINK, gtk.SHRINK)
    tableCameras.attach(gtk.Label('Remove only:'), 0, 1, 1, 2, gtk.SHRINK, gtk.SHRINK)
    tableCameras.attach(entryRemove, 1, 2, 1, 2, gtk.SHRINK, gtk.SHRINK)
    #Packing table in cameras related frame
    boxCameras = gtk.VBox(spacing = 10)
    boxCameras.set_border_width(10)
    boxCameras.pack_start(tableResolution)
    boxCameras.pack_start(tableCameras)
    frameCams.add(boxCameras)
    #Load variables
    labels = ('Filter K-size', 'Sigma (bilateral)', 'Morphology K-size',\
              'Butterworth order', 'Butterworth frequency', 'Minimums')
    ext_ = ((1, 199), (1, 199), (1, 199), (1, 199), (0.01, 1.00), (1, 199))
    lim_ = [[1, 21], [1, 150], [1, 21], [1, 15], [0.01, 1.00], [1, 11]]
    inc_ = (2, 1, 2, 2, .01, 2)
    def_ = (5, 50, 3, 3, 0.15, 1)
    adjMin = []
    adjMax = []
    adjDef = []
    spinMin = []
    spinMax = []
    spinDef = []
    #Elements for the defaults panels
    frameDefaults = gtk.Frame('Adjustments values')
    frameDefaults.set_border_width(5)
    tableDefaults = gtk.Table(7, 5, False)
    tableDefaults.set_border_width(10)
    tableDefaults.set_col_spacings(5)
    tableDefaults.set_row_spacings(2)
    tableDefaults.attach(gtk.Label('Values'), 0, 1, 0, 1)
    tableDefaults.attach(gtk.Label('Minimum'), 1, 2, 0, 1)
    tableDefaults.attach(gtk.Label('Maximum'), 2, 3, 0, 1)
    tableDefaults.attach(gtk.Label('Default'), 4, 5, 0, 1)
    tableDefaults.attach(gtk.VSeparator(), 3, 4, 0, 7)
    for i in xrange(6):
        adjMin.append(gtk.Adjustment(lim_[i][0], ext_[i][0], ext_[i][1], inc_[i], inc_[i], 0))
        adjMax.append(gtk.Adjustment(lim_[i][1], ext_[i][0], ext_[i][1], inc_[i], inc_[i], 0))
        adjDef.append(gtk.Adjustment(def_[i], ext_[i][0], ext_[i][1], inc_[i], inc_[i], 0))
        spinMin.append(gtk.SpinButton(adjMin[i], digits = 0 ) if i != 4 else gtk.SpinButton(adjMin[i], digits = 2)) 
        spinMax.append(gtk.SpinButton(adjMax[i], digits = 0 ) if i != 4 else gtk.SpinButton(adjMax[i], digits = 2))
        spinDef.append(gtk.SpinButton(adjDef[i], digits = 0 ) if i != 4 else gtk.SpinButton(adjDef[i], digits = 2))
        tableDefaults.attach(gtk.Label(labels[i]), 0, 1, i+1, i+2)
        tableDefaults.attach(spinMin[i], 1, 2, i+1, i+2)
        tableDefaults.attach(spinMax[i], 2, 3, i+1, i+2)
        tableDefaults.attach(spinDef[i], 4, 5, i+1, i+2)
        spinMin[i].connect('changed', on_change, (i, -1))
        spinMax[i].connect('changed', on_change, (i, 1))
        spinDef[i].connect('changed', on_change, (i, 0))
    frameDefaults.add(tableDefaults)
    
    boxMain = gtk.VBox(spacing = 10)
    boxMain.pack_start(frameCams)
    boxMain.pack_start(frameDefaults)
    
    dialog = gtk.Dialog("Default settings", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.vbox.pack_start(boxMain)
    boxMain.show_all()
    response = dialog.run()
    if response == gtk.RESPONSE_ACCEPT:
        OnAccept(None)
    dialog.destroy()
    return


def project_values(file_default, file_project):
    def OnChangeEntry(widget):
        text = widget.get_text().strip()
        if text.count('.') >= 2:
            widget.set_text(text[0: text.index('.')+1]+text[text.index('.')+1:len(text)].replace('.', ''))
        else:
            widget.set_text(''.join([i for i in text if i in '0123456789.']))
        return
    def OnLengthUnitChange(widget):
        for label in labelsUnits:
            label.set_text(widget.get_active_text())
        labelHeight.set_text(widget.get_active_text())
        return
    def OnAccept(widget, event=None):
        project_file.write('as-is','cameras', 'resolution', comboResolution.get_active_text())
        i_ = 0
        for cam in default_file.read('str', 'cameras', 'names'):
            if entriesDistance[i_].get_text() != '':
                project_file.write('as-is','geometry', cam, entriesDistance[i_].get_text())
            if entriesFocal[i_].get_text() != '':
                project_file.write('as-is','focal', cam, entriesFocal[i_].get_text())
            i_ += 1
        project_file.write('as-is','units', 'length', comboLength.get_active_text())
        project_file.write('as-is','units', 'mass', comboMass.get_active_text())
        if entryUser.get_text() != '':
                project_file.write('as-is','user', 'height', entryUser.get_text())
        return
    def SetActuals():
        value = project_file.read('list', 'cameras', 'resolution')
        if TryNone(value):
            value = default_file.read('list', 'cameras', 'resolution')
        if not TryNone(value):
            i_ = 0
            for res in default_file.read('list', 'cameras', 'supported_resolutions'):
                if value == res:
                    comboResolution.set_active(i_)
                    break
                i_ += 1
        i_ = 0
        for cam in default_file.read('str', 'cameras', 'names'):
            value = project_file.read('list', 'geometry', cam)
            if not TryNone(value):
                entriesDistance[i_].set_text(str(value))
            value = project_file.read('list', 'focal', cam)
            if not TryNone(value):
                entriesFocal[i_].set_text(str(value))
            i_ += 1
        value = project_file.read('str', 'units', 'length')
        if not TryNone(value):
            comboLength.set_active(lengthList.index(value[0]))
        value = project_file.read('str', 'units', 'mass')
        if not TryNone(value):
            comboMass.set_active(massList.index(value[0]))
        value = project_file.read('str', 'user', 'height')
        if not TryNone(value):
            entryUser.set_text(value[0])
        return
    def TryNone(value):
        return True if str(value).find('None') != -1 else False
    
    lengthList = ('mm', 'cm', 'm')
    massList = ('g', 'Kg')
    default_file = file_default
    project_file = file_project 
    
    comboResolution = gtk.combo_box_new_text()
    defRes = default_file.read('list', 'cameras', 'resolution')
    i_ = 0
    for res in default_file.read('list', 'cameras', 'supported_resolutions'):
        comboResolution.append_text(str(res))
        if defRes == res:
            comboResolution.set_active(i_)
        i_ += 1
    comboLength = gtk.combo_box_new_text()
    [comboLength.append_text(unit) for unit in lengthList]
    comboLength.set_active(0)
    comboMass = gtk.combo_box_new_text()
    [comboMass.append_text(unit) for unit in massList]
    comboMass.set_active(1)
    entryUser = gtk.Entry(4)
    labelHeight = gtk.Label(lengthList[0])
    
    tableConfiguration = gtk.Table()
    tableConfiguration.attach(gtk.Label('Resolution:'), 0, 1, 0, 1)
    tableConfiguration.attach(comboResolution, 1, 2, 0, 1)
    tableConfiguration.attach(gtk.HSeparator(), 0, 4, 1, 2)
    tableConfiguration.attach(gtk.Label('Length units:'), 0, 1, 2, 3)
    tableConfiguration.attach(comboLength, 1, 2, 2, 3)
    tableConfiguration.attach(gtk.Label('Mass units:'), 2, 3, 2, 3)
    tableConfiguration.attach(comboMass, 3, 4, 2, 3)
    tableConfiguration.attach(gtk.Label('User Height:'), 0, 1, 3, 4)
    tableConfiguration.attach(entryUser, 1, 3, 3, 4)
    tableConfiguration.attach(labelHeight, 3, 4, 3, 4)
    tableConfiguration.set_row_spacings(5)
    entryUser.connect('changed', OnChangeEntry)
    comboLength.connect('changed', OnLengthUnitChange)
    
    entriesDistance = []
    entriesFocal = []
    labelsCamera = []
    labelsUnits  = []
    tableCameras = gtk.Table(3, 5, False)
    tableCameras.attach(gtk.Label('Distance to Origin'), 1, 2, 0, 1)
    tableCameras.attach(gtk.Label('Focal length'), 3, 4, 0, 1)
    for i_ in xrange(3):
        entriesDistance.append(gtk.Entry(4))
        entriesFocal.append(gtk.Entry(4))
        labelsUnits.append(gtk.Label(lengthList[0]))
        tableCameras.attach(gtk.Label(default_file.read('str', 'cameras', 'names')[i_]+':'), 0, 1, i_+1, i_+2)
        tableCameras.attach(entriesDistance[i_], 1, 2, i_+1, i_+2)
        tableCameras.attach(labelsUnits[i_], 2, 3, i_+1, i_+2)
        tableCameras.attach(entriesFocal[i_], 3, 4, i_+1, i_+2)
        tableCameras.attach(gtk.Label('px'), 4, 5, i_+1, i_+2)
        entriesDistance[i_].connect('changed', OnChangeEntry)
        entriesFocal[i_].connect('changed', OnChangeEntry)
    tableCameras.set_row_spacings(3)
    
    boxMain= gtk.VBox(False, 15)
    boxMain.pack_start(tableConfiguration)
    boxMain.pack_start(tableCameras)
    dialog = gtk.Dialog("Project settings", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_modal(True)
    dialog.set_keep_above(True)
    dialog.vbox.pack_start(boxMain)
    boxMain.show_all()
    SetActuals()
    response = dialog.run()
    if response == gtk.RESPONSE_ACCEPT:
        OnAccept(None)
    dialog.destroy()
    return