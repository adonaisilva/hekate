#!/usr/bin/env python
# -*- coding: utf-8 -*-

from api_capture import camera, filter_pool, segment_pool
from multiprocessing import Process, Pipe
from types import IntType
from time import time


class permanent_shooter_tester(Process):
    '''
    Take pictures in the background from all selected cameras, send current RGB frames as requested
    '''
    def __init__(self, c_pipe, s_pipe):
        Process.__init__(self)
        self.__control_pipe = c_pipe
        self.__sending_pipe = s_pipe
        self.__cameras = [None] * 3
        self.__results = [None] * 3
        self.__control_data = 0 # -1 stop process, 0 don't send images, 1 send images
        self.__sending_data = [None] * 3
        return
    def run(self):
        'Take pictures from selected cameras'
        while self.__control_data != -1:
            #Run infinite loop as the main application is running
            for i, cam in enumerate(self.__cameras):
                #if there isn't a camera selected it creates a None value, otherwise create a RGB Matrix
                try:
                    cam(fast = False)
                    self.__results[i] = cam.RGBimage
                except:
                    self.__results[i] = None
            if self.__control_data:
                #Send list of RGB Matrix to main application only on request
                self.__sending_pipe.send(self.__results)
                self.__control_data = 0
            self.__sending_data = self.__sending_pipe.recv() if self.__sending_pipe.poll() else self.__sending_data
            for i, cam in enumerate(self.__cameras):
                #Change or close camera devices as selected on the main application
                if ((cam == None) and (self.__sending_data[i] != None)):
                    self.__cameras[i] = camera(self.__sending_data[i])
                elif ((cam != None) and (self.__sending_data[i] == None)):
                    self.__cameras[i].close()
                    self.__cameras[i] = None
                elif ((cam != None) and (cam.device != (self.__sending_data[i]))):
                    self.__cameras[i].close()
                    self.__cameras[i] = None
                    self.__cameras[i]= camera(self.__sending_data[i])
            self.__control_data = self.__control_pipe.recv() if self.__control_pipe.poll() else self.__control_data
        for cam in self.__cameras:
            try:
                cam.close()
            except:
                pass
        return


class permanent_shooter(Process):
    def __init__(self, c_pipe, s_pipe, default_file, project_file):
        Process.__init__(self)
        self.__c_pipe = c_pipe
        self.__s_pipe = s_pipe
        self.__d_file = default_file
        self.__p_file = project_file
        cam_names = default_file.read('str', 'cameras', 'names')
        resolution = project_file.read('list', 'cameras', 'resolution')
        self.__config = [project_file.read('list', 'cameras', cam) for cam in cam_names]
        self.__colors = [project_file.read('np_array', 'colors', cam) for cam in cam_names]
        cam_numbers = [config[0] for config in self.__config]
        self.__cameras = [camera(num, resolution) for num in cam_numbers]
        self.__c_data = 1 # -1 stop process, 0 pause process, 1 start-resume process
        self.__s_data = 0 # 0 don't send images, 1 send images
        self.__init_time = None
        self.__time = None
        #Setting workers
        self.__results = range(4)
        self.__flag = 0
        self.__c_pipes = []
        self.__s_pipes = []
        self.__workers = []
        for index in xrange(3):
            c_, c_1 = Pipe()
            s_, s_1 = Pipe()
            w_ = worker(self.__config[index], self.__colors[index], c_1, s_1) 
            w_.start()
            self.__c_pipes.append(c_)
            self.__s_pipes.append(s_)
            self.__workers.append(w_)
        return  
    def run(self):
        print self.name, "up"
        while self.__c_data != -1:
            self.__c_data = self.__c_pipe.recv() if self.__c_pipe.poll() else self.__c_data
            if self.__c_data == -1:
                break
            for cam in self.__cameras:
                cam(frame_delay = 0, fast = True)
            self.__s_data = self.__s_pipe.recv() if self.__s_pipe.poll() else self.__s_data
            if self.__s_data:
                if self.__init_time == None:
                    self.__init_time = time()
                for i in xrange(3):
                    self.__s_pipes[i].send(self.__cameras[i].HSVimage)
                self.__flag = 1
                self.__s_data = 0
            if self.__flag:
                for i in xrange(3):
                    if self.__s_pipes[i].poll():
                        self.__results[i] = self.__s_pipes[i].recv()
                        self.__flag += 1
                    if self.__flag == 4:
                        self.__flag = 0
                        self.__results[3] = time() - self.__init_time
                        self.__s_pipe.send(self.__results)                           
        print "closing", self.name
        for i_ in xrange(3):
            self.__c_pipes[i_].send(-1)
        return
     
class worker(Process):
    def __init__(self, config, color, c_pipe, s_pipe):
        Process.__init__(self)
        self.__c_pipe = c_pipe
        self.__s_pipe = s_pipe
        # -1 stop process, 0 pause process, 1 start-resume process
        self.__c_data = 1
        # 0 don't send images, != 0 send images
        self.__s_data = 0
        self.__filter = filter_pool(config[1:4])
        self.__segment = segment_pool(config[4:6], color)
        return
    def run(self):
        print self.name, "up"
        while self.__c_data != -1:
            self.__c_data = self.__c_pipe.recv() if self.__c_pipe.poll() else self.__c_data  
            if self.__c_data == -1:
                break
            self.__s_data = self.__s_pipe.recv() if self.__s_pipe.poll() else self.__s_data
            if type(self.__s_data) != IntType:
                result = self.__segment(self.__filter(self.__s_data))
                self.__s_pipe.send(result)
                self.__s_data = 0
        print self.name, "exiting"
        return