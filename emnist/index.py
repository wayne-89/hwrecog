#!/usr/local/bin/fontforge
# coding=utf-8
# file test.py

from mnist import MNIST
import cv2 as cv
import numpy as np


class EMNIST(object):
    path = None

    def __init__(self, path='.', name='enmist'):
        self.path = path
        self.name = name

    def getLabel(self, label):
        val = label
        if 10 <= label < 36:
            val = chr(label - 10 + ord('A'))
        elif label >= 36:
            val = chr(label - 36 + ord('a'))
        return str(val)

    def findMaxRectangleContours(self, contours):
        min_x, min_y = 28, 28
        max_x = max_y = 0
        for i in range(0, len(contours)):
            (x, y, w, h) = cv.boundingRect(contours[i])
            min_x, max_x = min(x, min_x), max(x + w, max_x)
            min_y, max_y = min(y, min_y), max(y + h, max_y)
        return min_x, min_y, max_x - min_x, max_y - min_y

    def offset(self, img, disp):
        im = np.array(img, dtype=np.uint8)
        ##################
        bw = cv.bitwise_not(im)
        if disp:
            cv.imwrite("./test_bw.png", bw)
        im2, contours, hierarchy = cv.findContours(bw, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        x, y, w, h = self.findMaxRectangleContours(contours)  # x y w h; x，y是矩阵左上点的坐标

        width = len(img[0])
        height = len(img)
        img_dc = cv.rectangle(bw, (x, y), (x + w, y + h), (255, 255, 255), 1)
        if disp:
            cv.imwrite("./test.png", img_dc)
        # if disp:
        #     exit(0)
        return x, height - (y + h), width - (x + w), y

    def load(self):
        path = self.path
        mndata = MNIST('./emnist/data', 'vanilla', 'numpy', True)
        mndata.select_emnist('byclass')
        # imgs, labels = mndata.load_testing()
        imgs, labels = mndata.load_training()

        # for i in range(len(imgs) - 10, len(imgs)):
        mat = []
        # for i in range(0, 1000):
        #     img2write = (255 - imgs[i]).reshape((28, 28))
        #     # print img2write.shape
        #     val = labels[i]
        #     if 10 <= labels[i] < 36:
        #         val = chr(labels[i] - 10 + ord('A'))
        #     elif labels[i] >= 36:
        #         val = chr(labels[i] - 36 + ord('a'))
        #     # if mat == 0:
        #     #     mat = img2write
        #     # else:
        #     #     mat = np.concatenate((mat, img2write), 0)
        #     # cv.imwrite('./result/' + str(i) + "--" + str(val) + '.png', img2write)
        #     print labels[i]
        page = 75  # 150
        pageSize = 20
        pageArea = pageSize * pageSize
        w = 28
        totalH = pageSize * w
        for k in range(0, page):
            matList = []
            output = open(path + '/eng.' + self.name + '.exp' + str(k + 1) + '.box', 'w')
            for j in range(0, pageSize):
                shapedList = []
                lastx = 0
                for i in range(0, pageSize):
                    index = k * pageArea + j * pageSize + i
                    shape = (255 - imgs[index]).reshape(w, w)
                    disp = False
                    ofx1, ofy1, ofx2, ofy2 = self.offset(shape, disp)
                    shapedList.append(shape)
                    label = self.getLabel(labels[index])
                    x1 = i * w + ofx1
                    x2 = (i + 1) * w - ofx2
                    y1 = totalH - (j + 1) * w + ofy1
                    y2 = totalH - j * w - ofy2
                    if i != 0:
                        # 每个单词前添加空格
                        output.write(
                            " " + " " + str(lastx) + " " + str(y1) + " " + str(x1) + " " + str(y2) + " 0\n")
                    output.write(label + " " + str(x1) + " " + str(y1) + " " + str(x2) + " " + str(y2) + " 0\n")
                    if i == pageSize - 1:
                        # 每行最后一个
                        output.write(
                            "\t" + " " + str(x2) + " " + str(y2) + " " + str(x2 + 1) + " " + str(y2 + 1) + " 0\n")
                    lastx = x2
                mat = np.concatenate(tuple(shapedList), 1)
                matList.append(mat)
            result = np.concatenate(tuple(matList), 0)
            # mat = np.concatenate((imgs[0].reshape((28, 28)), imgs[1].reshape((28, 28)), imgs[2].reshape((28, 28))), 1)
            cv.imwrite(path + '/eng.' + self.name + '.exp' + str(k + 1) + '.tif', result)
            output.close()
        return 0, page
        # which = 0
        # for img in imgs:
        #     img2write = img.reshape((28, 28))
        #     cv.imwrite('./result/' + str(which) + '.png', img2write)
        #     which = which + 1

        # print('Showing id {}, num: {}'.format(which, img[which]))
        # print(mndata.display(img[which]))
