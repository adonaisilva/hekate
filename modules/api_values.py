#!/usr/bin/env python
#-*- coding: utf-8 -*-

from random import randint
from types import NoneType
from numpy import zeros_like
from cv2 import split, merge
from Crypto.Util.number import size

class randoms(object):
    def __init__(self):
        self.position = []
        self.velocity = []
        self.acceleration = []
        self.torque = []
        for index in xrange(4):
            self.position.append(randint(-256, 256))
            self.velocity.append(randint(-256, 256))
            self.acceleration.append(randint(-256, 256))
            self.torque.append(randint(-256, 256))
        del(index)

class masked_image(object):
    def __init__(self, image, filled, checks = (True, True, True)):
        mask = zeros_like(filled[0])
        for i in xrange(3):
            if checks[i]:
                mask = mask | filled [i]
        (b, g, r) = split(image)   
        self.image = merge((r & mask, g & mask, b & mask))
        return