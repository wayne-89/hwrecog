# coding=utf-8
# !/usr/bin/env python

'''
Floodfill sample.
Usage:
  floodfill.py [<image>]
  Click on the image to set seed point
Keys:
  f     - toggle floating range
  c     - toggle 4/8 connectivity
  ESC   - exit
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2 as cv
import sys
import os
from node import Node


def readTemplate():
    ''' 读取模板数据， 注意： 模板第一行为行数 列数 需要训练的行数 需要训练的列数'''
    file = open('template.txt')
    list_of_all_the_lines = file.read().splitlines()
    allChars = []
    for line in list_of_all_the_lines:
        chars = line.split(" ")
        allChars.append(chars)
        # print(line)
    rowNum = int(allChars[0][0])
    colNum = int(allChars[0][1])
    detectRowNum = int(allChars[0][2])
    detectColNum = int(allChars[0][3])
    template = allChars[1:]
    print(template)
    return rowNum, colNum, detectRowNum, detectColNum, template


def initOutput(filename):
    path = './output/' + filename
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
    return path + '/'


def getFilePath(filename, imagename):
    return initOutput(filename) + imagename


def writeBoxFile(template, boxInfo, filename, imgHeight):
    '''将模板数据很检测到的位置信息写入文件box'''
    output = open(getFilePath(filename, 'eng.' + filename + '.exp1.box'), 'w')
    for i in range(0, min(len(template), len(boxInfo))):  # 行
        for j in range(0, min(len(template[i]), len(boxInfo[i]))):  # 列
            box = boxInfo[i][j]
            print(box)
            if box is not None and box != 0:
                output.write(
                    template[i][j] + " " + str(box.x) + " " + str(imgHeight - box.y - box.h) + " " + str(
                        box.x + box.w) + " " + str(imgHeight - box.y) + " 0\n")
                if j == min(len(template[i]), len(boxInfo[i])) - 1:
                    # output.write(
                    #     "" + " " + str(box.x + 1) + " " + str(imgHeight - box.y - box.h) + " " + str(
                    #         box.x + box.w) + " " + str(imgHeight - box.y) + " 0\n")
                    output.write(
                        "\t" + " " + str(box.x + box.w) + " " + str(imgHeight - box.y) + " " + str(
                            box.x + box.w + 1) + " " + str(imgHeight - box.y + 1) + " 0\n")
                else:
                    nextbox = boxInfo[i][j + 1]
                    if nextbox != 0:
                        output.write(
                            " " + " " + str(box.x + box.w - 1) + " " + str(imgHeight - box.y - box.h) + " " + str(
                                nextbox.x) + " " + str(imgHeight - box.y) + " 0\n")

    output.close()


def doIntercept(filename):
    # 读取模板文件
    rowNum, colNum, detectRowNum, detectColNum, template = readTemplate()

    img = cv.imread(filename + '.tif', 1)  # 0表示灰度
    img_src = img.copy()
    img_dc = img.copy()

    img = cv.GaussianBlur(img, (11, 11), 0)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    outerBox = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 5, 2)
    bw = cv.bitwise_not(outerBox)
    # 膨胀 ############
    # 构造一个5×5的结构元素
    element = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    cv.imwrite(getFilePath(filename, 'bw.png'), bw)

    dilate = cv.dilate(bw, element)
    cv.imwrite(getFilePath(filename, 'dilate.png'), dilate)

    erode = cv.erode(dilate, element)
    cv.imwrite(getFilePath(filename, 'erode.png'), erode)

    ##################
    im2, contours, hierarchy = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    # print(img.shape)

    # img = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)  # 生成一个空彩色图像
    # 最大内轮廓
    img_dc = cv.drawContours(img_dc, contours, 1, (0, 255, 0), 1)
    # 获取4点坐标
    boundRect = cv.boundingRect(contours[1])
    cha = 2
    bound = [boundRect[0] + cha, boundRect[1] + cha, boundRect[2] - cha, boundRect[3] - cha]
    # cv.imshow('image2', img_dc)
    # 分割每个字符，计算box###########

    colWidth = bound[2] / colNum
    rowHeight = bound[3] / rowNum

    boxTable = [[0 for i in range(colNum)] for j in range(rowNum)]
    # cv.imshow('image', img[58:58 + bound[3], 67:67 + bound[2], :])
    img_inner = img_src[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2], :].copy()
    img_inner_src = img_inner.copy()
    # cv.imshow('imagesss', img_inner)
    for j in range(0, detectRowNum):
        for i in range(0, detectColNum):
            # roi 先y轴再x轴
            y = bound[1] + j * rowHeight
            x = bound[0] + i * colWidth
            roi = erode[y:y + rowHeight,
                  x:x + colWidth]
            # roi_rgb = img_dc[y:y + rowHeight,
            #           x:x + colWidth, :]
            imInner, contoursInner, hierarchyInner = cv.findContours(roi, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            # img_dc_inner = cv.drawContours(roi_rgb, contoursInner, 0, (0, 255, 0), 1)
            if len(contoursInner) > 0:
                boundRectInner = cv.boundingRect(contoursInner[0])
                # img_dc_inner = cv.rectangle(roi_rgb, (boundRectInner[0], boundRectInner[1]),
                #                             (boundRectInner[0] + boundRectInner[2], boundRectInner[1] + boundRectInner[3]),
                #                             (0, 255, 0), 1)
                # print(boundRectInner)
                node = boxTable[j][i] = Node(x + boundRectInner[0] - bound[0],
                                             y + boundRectInner[1] - bound[1],
                                             boundRectInner[2],
                                             boundRectInner[3])
                # print(node.x, node.y, node.w, node.h)
                img_inner = cv.rectangle(img_inner, (node.x, node.y),
                                         (node.x + node.w, node.y + node.h),
                                         (0, 255, 0), 1)
                # cv.imshow('image' + str(j + 1) + "," + str(i + 1), img_dc_inner)
            else:
                boxTable[j][i] = None
                # cv.imshow('image' + str(j + 1) + "," + str(i + 1), roi_rgb)
    cv.imwrite(getFilePath(filename, 'result.png'), img_inner)
    cv.imwrite(getFilePath(filename, 'eng.' + filename + '.exp1.tif'), img_inner_src)
    # ################################

    # 输出box文件
    writeBoxFile(template, boxTable, filename, img_inner.shape[0])
    return True
    # cv.waitKey(0)
    # cv.destroyAllWindows()
