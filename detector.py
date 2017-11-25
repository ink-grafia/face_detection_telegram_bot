# -*- coding: utf-8 -*-
import numpy as np
import cv2
import os

import config
from user import user


class Detector:
    def __init__(self):
        self.haarcascades = []
        folder = os.path.join(os.path.dirname(__file__)) + '/haarcascades/'
        for filename in os.listdir(folder):
            self.haarcascades.append(self.get_haarcascade(folder + filename))
            #self.users['user_token'] = None # user_token for getting his haarcascade

        self.vertical_spacing = 1 / 3  # of face height
        self.horizontal_spacing = 1 / 3  # of fave width

    def detect_head(self, img: np.ndarray, usr: user):
        if not usr.haarcascade:
            self.default_haarcascade_for_user(usr)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = usr.haarcascade.detectMultiScale(gray, 1.3, 5) #TODO fix for different users

        for (x, y, w, h) in faces:
            old_start = (0, 0)
            old_end = img.shape

            #x = x - (h-w/config.ratio)/2
            h = w/config.ratio
            #y = y + (w - config.ratio * h)/2
            #w = w - (w - config.ratio * h)/2

            new_x_start = old_start[1] if old_start[1] > x - w * self.horizontal_spacing \
                else x - w * self.horizontal_spacing

            new_y_start = old_start[0] if old_start[0] > y - h * self.vertical_spacing \
                else y - h * self.vertical_spacing


            new_start = (int(new_y_start), int(new_x_start))

            mb_x = x + w + int(w * self.horizontal_spacing)
            mb_y = y + h + int(h * self.vertical_spacing)
            new_x_end = old_end[1] if old_end[1] < mb_x else mb_x
            new_y_end = old_end[0] if old_end[0] < mb_y else mb_y
            new_end = (int(new_y_end), int(new_x_end))

            img = img[new_start[0]:new_end[0], new_start[1]:new_end[1]]
            return img

    def get_haarcascade(self, path: str):
        return cv2.CascadeClassifier(path)

    def next_haarcascade_for_user(self, usr: user):
        usr.tries+=1
        usr.haarcascade = self.haarcascades[usr.tries]

    def default_haarcascade_for_user(self, usr: user):
        usr.haarcascade = self.haarcascades[0]