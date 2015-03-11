# -*- coding: utf-8 -*-
from math import sqrt, atan, sin, cos, pi
'''
@author: osiris
'''

class triangulator(object):
    '''
    classdocs
    '''

    def __init__(self, resolution, distances):
        '''
        Constructor
        '''
        self.image_center = (resolution[0]/2, resolution[1]/2)
        self.focal_length = []
        self.dist_to_center = []
        for cam in distances:
            self.focal_length.append(cam[0])
            self.dist_to_center.append(cam[1])
        self.L = []
        self.L.append(sqrt(self.dist_to_center[0]**2 + self.dist_to_center[1]**2))
        self.L.append(sqrt(self.dist_to_center[0]**2 + self.dist_to_center[2]**2))
        self.L.append(sqrt(self.dist_to_center[1]**2 + self.dist_to_center[2]**2))
        self.t1 = []
        self.t1.append(atan(self.dist_to_center[0]/self.dist_to_center[1]))
        self.t2 = []
        self.t2.append(atan(self.dist_to_center[1]/self.dist_to_center[0]))
        return
   
    def __call__(self, centroids):
        '''
        '''
        self.c_f_s=[]
        for i_ in xrange(3):
            for j_ in xrange(3):
                if (not (None in centroids[i_][j_][0])):
                    centroids[i_][j_][0][0] -= self.image_center[0]
                    centroids[i_][j_][0][1] -= self.image_center[1] 
        self._front_side(centroids)
    def __str__(self):
        '''
        '''
        return
    
    def __del__(self):
        '''
        '''
        return
    
    def _front_side(self,centroids):
        '''
        '''
        for i in xrange(3):
            if not ((None in centroids[0][i][0]) | (None in centroids[1][i][0])) :
                alphap = atan(-centroids[0][i][0][0]/self.focal_length[0])
                bethap = atan(centroids[1][i][0][0]/self.focal_length[1])
                alpha = self.t1[0]-alphap
                betha = self.t2[0]-bethap
                miu = pi-betha-alpha
                h1 = self.L[0]*sin(betha)/sin(miu)
                h2 = self.L[0]*sin(alpha)/sin(miu)
                x = h2*sin(bethap)
                y = h1*sin(alphap)
                z = centroids[0][i][0][1]*(self.dist_to_center[0]-x)/self.focal_length[0]
                self.c_f_s.append([int(round(x)), int(round(y)), int(round(z))])
            else:
                self.c_f_s.append([None, None, None])
        print self.c_f_s
        return
    
    def _front_top(self):
        '''
        '''
        return
    
    def _side_top(self):
        '''
        '''
        return