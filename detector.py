import numpy as np
import cv2
import os


class Detector:
    def __init__(self):
        self.haarcascades = []
        folder = os.path.join(os.path.dirname(__file__)) + '/haarcascades/'
        for filename in os.listdir(folder):
            self.haarcascades.append(folder + filename)
        self.current_haarcascade = 2  # will be incremented for first
        self.next_haarcascade()
        self.vertical_spacing = 1 / 3  # of face height
        self.horizontal_spacing = 1 / 3  # of fave width

    def detect_head(self, img: np.ndarray):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            old_start = (0, 0)
            old_end = img.shape

            new_x_start = old_start[1] if old_start[1] > x - w * self.horizontal_spacing \
                else x - w * self.horizontal_spacing
            new_y_start = old_start[0] if old_start[0] > y - h * self.vertical_spacing \
                else y - h * self.vertical_spacing
            new_start = (int(new_y_start), int(new_x_start))

            mb_x = x + w + int(w * self.horizontal_spacing)
            mb_y = y + h + int(h * self.vertical_spacing)
            new_x_end = old_end[1] if old_end[1] < mb_x else mb_x
            new_y_end = old_end[0] if old_end[0] < mb_y else mb_y
            new_end = (new_y_end, new_x_end)

            img = img[new_start[0]:new_end[0], new_start[1]:new_end[1]]
            return img

    def next_haarcascade(self):
        self.current_haarcascade += 1
        self.face_cascade = cv2.CascadeClassifier(self.haarcascades[self.current_haarcascade])
