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


def writeBoxFile(template, boxInfo, filename, image):
    '''将模板数据很检测到的位置信息写入文件box'''
    imgHeight = image.shape[0]
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


def writeCharImg(template, boxInfo, filename, image):
    '''将模板数据很检测到的图片存储'''
    output = open(getFilePath(filename + '/chars', 'map_file.txt'), 'w')
    index = 0
    for i in range(0, min(len(template), len(boxInfo))):  # 行
        for j in range(0, min(len(template[i]), len(boxInfo[i]))):  # 列
            box = boxInfo[i][j]
            if box is not None and box != 0:
                char_img = image[box.y:box.y + box.h, box.x:box.x + box.w]
                cv.imwrite(getFilePath(filename + '/chars', str(index) + '.png'), char_img)
                output.write(
                    str(index) + " " + template[i][j] + "\n")
                index += 1
    output.close()


def findMaxAreaContours(contours):
    maxAreaI = 0
    maxArea = 0
    for i in range(0, len(contours)):
        area = cv.contourArea(contours[i])
        if area > maxArea:
            maxAreaI = i
            maxArea = area
    # print('maxAreaI: ' + str(maxAreaI) + ' area: ' + str(maxAreaI))
    return maxAreaI


def doIntercept(filename, basePath, method):
    # 读取模板文件
    rowNum, colNum, detectRowNum, detectColNum, template = readTemplate()

    img = cv.imread(basePath + '/' + filename + '.tif', 1)  # 0表示灰度
    img_src = img.copy()
    img_dc = img.copy()

    img = cv.GaussianBlur(img, (11, 11), 0)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    outerBox = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 5, 2)
    bw = cv.bitwise_not(outerBox)
    # 膨胀 ############
    # 构造一个5×5的结构元素
    print(int(img.shape[1] * 0.015))
    scale = int(img.shape[1] * 0.015)
    element = cv.getStructuringElement(cv.MORPH_RECT, (scale, scale))
    cv.imwrite(getFilePath(filename, 'bw.png'), bw)

    dotscale = int(img.shape[1] * 0.002)
    print('dotscale ' + str(dotscale))
    dotelement = cv.getStructuringElement(cv.MORPH_RECT, (dotscale, dotscale))
    bw = cv.erode(bw, dotelement)
    cv.imwrite(getFilePath(filename, 'dotscale1.png'), bw)
    bw = cv.dilate(bw, dotelement)
    cv.imwrite(getFilePath(filename, 'dotscale2.png'), bw)

    dilate = cv.dilate(bw, element)
    cv.imwrite(getFilePath(filename, 'dilate.png'), dilate)

    erode = cv.erode(dilate, element)
    cv.imwrite(getFilePath(filename, 'erode.png'), erode)

    ##################
    im2, contours, hierarchy = cv.findContours(dilate, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    # print(img.shape)
    maxAreaI = findMaxAreaContours(contours)
    # img = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)  # 生成一个空彩色图像
    # 最大轮廓

    img_dc = cv.drawContours(img_dc, contours, maxAreaI, (0, 255, 0), 1)
    cv.imwrite(getFilePath(filename, 'drawcontours.png'), img_dc)

    # 获取4点坐标
    boundRect = cv.boundingRect(contours[maxAreaI])
    cha = max(2, boundRect[2] / 100 + scale)
    innercha = int(cha / 18)
    print(cha)
    bound = [boundRect[0] + cha, boundRect[1] + cha, boundRect[2] - cha * 2, boundRect[3] - cha * 2]
    # cv.imshow('image2', img_dc)
    # cv.imwrite(getFilePath(filename, 'img_dc.png'), img_dc)
    # cv.waitKey(0)
    # cv.destroyAllWindows()
    # 分割每个字符，计算box###########

    colWidth = bound[2] / colNum
    rowHeight = bound[3] / rowNum

    bw_fine_result = bw.copy()
    bw_fine_result[:] = 255
    boxTable = [[0 for i in range(colNum)] for j in range(rowNum)]
    img_inner = img_src[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2], :].copy()
    bw_fine_inner_result = bw_fine_result[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2]]
    bw_inner_src = outerBox[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2]]

    cv.imwrite(getFilePath(filename, 'bw_inner_src.png'), bw_inner_src)
    for j in range(0, detectRowNum):
        for i in range(0, detectColNum):
            # roi 先y轴再x轴
            y = bound[1] + j * rowHeight
            x = bound[0] + i * colWidth
            roi = erode[y:y + rowHeight,
                  x:x + colWidth]
            # bw_fine_result[y:y + rowHeight, x:x + colWidth] = outerBox[y:y + rowHeight,
            #                                                  x:x + colWidth]
            imInner, contoursInner, hierarchyInner = cv.findContours(roi, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            # img_dc_inner = cv.drawContours(roi_rgb, contoursInner, 0, (0, 255, 0), 1)
            if len(contoursInner) > 0:
                maxAreaI = findMaxAreaContours(contoursInner)
                boundRectInner = cv.boundingRect(contoursInner[maxAreaI])
                node = boxTable[j][i] = Node(x + boundRectInner[0] - bound[0],
                                             y + boundRectInner[1] - bound[1],
                                             boundRectInner[2],
                                             boundRectInner[3])
                img_inner = cv.rectangle(img_inner, (node.x, node.y),
                                         (node.x + node.w, node.y + node.h),
                                         (0, 255, 0), 1)
                bw_fine_inner_result[node.y:node.y + node.h, node.x:node.x + node.w] = bw_inner_src[
                                                                                      node.y:node.y + node.h,
                                                                                      node.x:node.x + node.w]

            else:
                boxTable[j][i] = None
    # cv.imwrite(getFilePath(filename, 'empty.png'), bw_fine_result)
    cv.imwrite(getFilePath(filename, 'result.png'), img_inner)
    cv.imwrite(getFilePath(filename, 'result_for_box.tif'), bw_fine_inner_result)
    # ################################
    # exit(0)
    if method == 1:
        # 输出box文件
        writeBoxFile(template, boxTable, filename, bw_fine_inner_result)
    else:
        # 输出chars字体所需图片和map文件
        writeCharImg(template, boxTable, filename, bw_fine_inner_result)

    return True
    # cv.waitKey(0)
    # cv.destroyAllWindows()
