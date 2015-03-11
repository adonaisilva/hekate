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
from reportlab.graphics.shapes import rotate

'''
Cross-module variables:
                        __builtin__.MOD_PATH = modules path
                        __builtin__.MEDIA_PATH = media path
                        __builtin__.MAIN_PATH = main path
                        __builtin__.META = Metadata XML root
'''
from cv2 import (drawContours, getStructuringElement, moments, VideoCapture, cvtColor,
                 blur, medianBlur, bilateralFilter, inRange, morphologyEx, findContours,
                 MORPH_RECT, CHAIN_APPROX_SIMPLE, RETR_EXTERNAL)
from cv2.cv import CV_CAP_PROP_FRAME_WIDTH, CV_CAP_PROP_FRAME_HEIGHT, CV_BGR2HSV, CV_BGR2RGB 
from numpy import array, uint8, zeros,  histogram, where, max, gradient, abs, sign, ones
from scipy.signal import filtfilt, butter
from math import sqrt, atan, sin, cos, pi
from time import time


class camera(object):
    '''
    Object containing camera information
    Call-able, retrieve current frame in camera buffer
    
    User accessible attributes:
        device        system device number
        resolution    camera resolution
        BGRimage      image in BGR format
        HSVimage      image in HSV format
        RGBimage      image in RGB format
        FPS           camera speed in FPS
        
    User accessible methods:
        close         close camera device
    '''
    def __init__(self, cam_num = -1, resolution = (640, 480)):
        '''
        create camera object
            cam_num            device number (integer)
            resolution         image resolution (tuple width x height)
        '''
        self.device = cam_num
        self.resolution = resolution
        self.BGRimage = []
        self.HSVimage = []
        self.RGBimage = []
        self.FPS = [0, 0]
        self.__avr = 0
        #assign and open device
        self.__capture = VideoCapture(cam_num)
        self.__capture.set(CV_CAP_PROP_FRAME_WIDTH,resolution[0])
        self.__capture.set(CV_CAP_PROP_FRAME_HEIGHT,resolution[1])
        self.__capture.open
        self.__flag = False
        t0 = time()
        self.__flag, self.BGRimage = self.__capture.read()
        self.FPS[0] = 1/(time()-t0)
        self.FPS[1] = self.FPS[0]
        self.__avr = self.FPS[0]
        print "camera", self.device, "ready @", self.FPS[0], "fps"
        return
    def __call__(self, frame_delay = 0, fast = False):
        '''
        retrieve current frame in camera buffer
            frame_delay        delay the frame decoding (integer)
            fast               if true don't decode image to RGB format (logic)    
        '''
        #set timer to meassure fps
        self.__avr = self.FPS[1]
        t0 = time()
        #try to retrieve current frame
        while not self.__flag:
            if frame_delay > 0:
                for i in xrange(frame_delay + 1):
                    self.__capture.grab()
                self.__flag, self.BGRimage = self.__capture.retrieve()
                del i
            else:
                self.__flag, self.BGRimage = self.__capture.read()
        self.__flag = False
        #decode bgr format to hsv
        self.HSVimage = cvtColor(self.BGRimage, CV_BGR2HSV)
        if fast:
            self.FPS[0] = 1/(time()-t0)
            self.FPS[1] = (self.FPS[0]+self.__avr)/2
            return
        #decode bgr format to rgb
        self.RGBimage = cvtColor(self.BGRimage, CV_BGR2RGB)
        self.FPS[0] = 1/(time()-t0)
        self.FPS[1] = (self.FPS[0]+self.__avr)/2
        return
    def __str__(self):
        '''
        return camera information;
            device number
            device resolution
            instant speed
            average speed
        '''
        tmp = "camera object @ dev "+str(self.device)+", resolution: "+str(self.resolution)
        tmp = tmp +", fps: "+str(self.FPS[0])+", Avr. fps: "+str(self.FPS[1])
        return tmp
    def __del__(self):
        '''
        when the object is deleted, it closes the device
        '''
        self.close()
        return
    def close(self):
        '''
        close device, making it available to use 
        '''
        #if the device is open then close it
        if self.__capture.isOpened():
            self.__capture.release()
            print "camera", self.device, "closed"
        return


class thresholder(object):
    '''
    object that calculate the threshold of a subimage
    Call-able, calculate threshold of given subimage
    
    User accessible attributes:
        CTR            central value of color histogram
        MIN            minimal value of color histogram
        MAX            maximum value of color histogram
    
    User accessible method:
        update_confg   update the filter configuration
    '''
    def __init__(self, config):
        '''
        Create thresholder object
            config        configuration for butterworth filter (list [order{integer none}, 
                                    frequency{0-1}, mimimum {integer none}])
        '''
        self.__hsv_max = (180, 255, 255)
        self.update_config(config)
        return
    def __call__(self, sub):
        '''
        Find the highest concentration concentration of color in a subimage and return limits
            of that region
        '''
        #an array for each value for each HSV component
        self.CTR = array([0, 0 ,0], uint8)
        self.MIN = array([0, 0, 0], uint8)
        self.MAX = array([0, 0, 0], uint8)
        self.__hist = []
        self.__hist_smooth =[]
        self.__d1hist = []
        #if the selected area is too small send warning 
        if sub == None:
            print 'Select a bigger area'
            return
        for i in range(3):
            #create histogram for each subimage hsv component
            self.__hist.append(histogram(sub[:,:,i], range(self.__hsv_max[i]+1))[0])
            #filter the histogram to obtain the highest concentration of color 
            self.__hist_smooth.append(self.__low_butter(self.__hist[i]))
            #for the filtered histrogram obtain the gradient
            self.__d1hist.append(gradient(self.__hist_smooth[i]))
            #find the peak signal of the histogram
            CTR = where(self.__hist[i] == max(self.__hist[i]))[0]
            try:
                self.CTR[i] = CTR[0] if CTR[0] != 0 else CTR[1]
            except:
                self.CTR[i] = 1
        #obtain the min an max values of color                     
        self.__limit_smooth()
        return
    def __limit_smooth(self):
        '''
        find limits of a highest concentration of color, it work by the assumption of a zero crossing
            in the gradient histogram 
        '''
        for i in range(3):
            zero_cross = where(sign(self.__d1hist[i][1:]) != sign(self.__d1hist[i][:-1]))[0]
            near_index = self.__find_nearest(zero_cross, self.CTR[i])
            self.MIN[i] = 0 if near_index < self.__minimum else zero_cross[near_index - self.__minimum]
            self.MAX[i] = self.__hsv_max[i] if near_index > zero_cross.shape[0] -\
                    (self.__minimum + 1) else zero_cross[near_index + self.__minimum]  
        return           
    def __find_nearest(self, array, value):
        '''
        find the closest equal value in a list of values
        '''
        idx = (abs(array-value)).argmin() 
        return where(array == array[idx])[0]
    def __low_butter(self, x):
        '''
        filter a histogram to eliminate high frequencies (noise or small peaks of color)
        '''
        b, a = butter(self.__order, self.__freq)
        return filtfilt(b, a, x)
    def update_config(self, config):
        '''
        update the configuration of the filter
        '''
        self.__order = config[0]
        self.__freq = config[1]
        self.__minimum = config[2]
        return


class filter_pool(object):
    '''
    object that filter the current image whit the selected method
    call-able return the filtered image
    
    user accessible methods:
        update_config        update the filter configuration
    '''
    def __init__(self, config):
        '''
        create object that filter images and return the filtered image whit the selected method
            config    configuration for the selected method (list [kernel size{integer none},
                            sigma{integer}, method{integer}])
        '''
        self.update_config(config)
        return
    def __call__(self, image):
        '''
        return filtered image
        '''
        if self.__f_type == 0:
            #filter with median blur
            filtered = medianBlur(image, self.__f_ksize)
        elif self.f_type == 1:
            #filter with average blur
            filtered = blur(image, (self.__f_ksize, self.__f_ksize))
        elif self.f_type == 2:
            #filter with gaussian blur
            filtered = bilateralFilter(image, self.__f_ksize, self.__sigma, self.__sigma)
        return filtered
    def update_config(self, config):
        '''
        update the configuration of the filter
        '''
        self.__f_ksize = config[0]
        self.__sigma = config[1]
        self.__f_type = config[2]
        return


class segment_pool(object):
    '''
    object that segment the current image whit the selected method
    call-able return the centroid of each or single segment and segmented image(binary)
    
    user accessible methods:
        update_config        update the filter configuration
    '''
    def __init__(self, config, color):
        '''
        create object that segment a image with the given colors 
            config        filter configuration (list [kernel size{integer none}, 
                                contour{logic}])
            color         color previously calculated with thresholder (list 1*9 integers)
        '''
        self.update_config(config, color)
        return
    def __call__(self, filtered):
        '''
        return centroids and segmented image(binary)
        '''
        centroid = []
        filled = []
        for i_ in xrange(3):
            c = []
            #create image with only the color values between the min and max
            thresholded = inRange(filtered, self.__color[(3*i_)+1], self.__color[(3*i_)+2])
            #apply morphology to the binary image (erode-dilate)
            thresholded = (morphologyEx(thresholded, 2, self.__structure)).astype('uint8')
            #find the closed contours
            cs, _ = findContours(thresholded, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE )
            fill = zeros(thresholded.shape[0:2]).astype('uint8')
            #find and draw the biggest contour in the image
            if not self.__contour:
                maximus = []
                for index in xrange(len(cs)):
                    maximus.append(len(cs[index]))
                try:
                    m = moments(cs[where(maximus == max(maximus))[0][0]])
                    #find the mass center (centroid)
                    c.append([m['m10'] / m['m00'], m['m01'] / m['m00']])
                except:
                    c.append([None, None])    
                try:        
                    drawContours(fill, cs, where(maximus == max(maximus))[0][0], 255, -1 )
                except:
                    fill = None
            #draw all contours
            else:
                for index in xrange(len(cs)):
                    m = moments(cs[index])
                    try:
                        #find the mass center (centroid)
                        c.append([m['m10'] / m['m00'], m['m01'] / m['m00']])
                    except:
                        c.append([None, None])
                try:
                    drawContours(fill, cs, -1, 255, -1 )
                except:
                    fill = None
            centroid.append(c)
            filled.append(fill) 
        return [centroid, filled]
    def update_config(self, config, color):
        '''
        update the configuration of the filter
        '''
        self.__m_ksize = config[0]
        self.__contour = config[1]
        self.__color = color
        self.__structure = getStructuringElement(MORPH_RECT, (self.__m_ksize, self.__m_ksize))
        return
      
class triangulator(object):
    '''
    classdocs
    '''

    def __init__(self, resolution, distances):
        '''
        Constructor
        '''
        r0 = resolution[0]/2
        r1 = resolution[1]/2
        self.__sign_cam = [[-1, -1], [1, -1], [1, -1]]
        self.__center = [[r0, r1], [-r0, r1], [-r0, r1]]
        self.__focal = [cam[0] for cam in distances]
        self.__to_center = [cam[1] for cam in distances]
        self.__rotate = [[0, 0], [1, 1], [1, 0]]
        self.__order = [[1, 0, 2], [1, 2, 0], [0, 2, 1]]  
        return
   
    def __call__(self, centroids):
        '''
        '''
        coordinates = zeros(3)
        operation, centroids = self.__retrieve(centroids)
        if (False in operation):
            print 'Not enough data to calculate'
            return None
        for i_ in xrange(3):
            centroid = centroids[:][i_][:]
            focal = self.__focal
            to_center = self.__to_center
            rotate = self.__rotate[operation[i_]-1][:]
            order = self.__order[operation[i_]-1][:]
            del centroid[3-operation[i_]][:]
            del focal[3-operation[i_]]
            del to_center[3-operation[i_]]
            coordinates[i_] = self.__triangulate(centroid, focal, to_center, rotate, order)
        return coordinates
        
    def __retrieve(self, centroids):
        centroids = centroids[:][:][0][:]
        viable = ones(3, 3)*False
        operation = ones(3)*False
        print centroids
        for i_ in xrange(3):
            for j_ in xrange(3):
                if (None in centroids[i_][j_]):
                    viable[i_][j_] = False
                elif (not (None in centroids[i_][j_])):
                    viable[i_][j_] = True
                    centroids[i_][j_][0] = self.__sign_cam[i_][0] * centroids[i_][j_][0] + self.__center[i_][0]
                    centroids[i_][j_][1] = self.__sign_cam[i_][1] * centroids[i_][j_][1] + self.__center[i_][1]
        print viable
        for k_ in xrange(3):
            if viable[0][k_] and viable[1][k_]:
                operation[k_] = 1
            elif viable[0][k_] and viable[2][k_]:
                operation[k_] = 2
            elif viable[1][k_] and viable[2][k_]:
                operation[k_] = 3
            else:
                operation[k_] = False
        print operation
        return operation, centroids
    
    def __triangulate(self, centroids, focal, to_center, rotate, order):
        '''
        '''
        L = sqrt(to_center[0]**2 + to_center[1]**2)
        t1 = atan(to_center[0]/to_center[1])
        t2 = atan(to_center[1]/to_center[0])
        alphap = atan(centroids[0][rotate[0]]/focal[0])
        bethap = atan(centroids[1][rotate[1]]/focal[1])
        alpha = t1-alphap
        betha = t2-bethap
        miu = pi-betha-alpha
        h1 = L*sin(betha)/sin(miu)
        h2 = L*sin(alpha)/sin(miu)
        x = h2*sin(bethap)
        y = h1*sin(alphap)
        z = (centroids[0][not rotate[0]])*(to_center[0]-x)/focal[0]
        results = [int(round(x)), int(round(y)), int(round(z))]
        return [results[i] for i in order]