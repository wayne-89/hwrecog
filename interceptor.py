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
import re
import cv2 as cv
import sys
import os
from node import Node
from template import Template


def readTemplate():
    ''' 读取模板数据， 注意： 模板第一行为行数 列数 需要训练的行数 需要训练的列数'''
    file = open('template.txt')
    list_of_all_the_lines = file.read().splitlines()
    allChars = []
    for line in list_of_all_the_lines[2:]:
        chars = re.split(r'[\s]', line)
        # chars = line.split(" ")
        allChars.append(chars)
        # print(chars)
    # print(allChars)
    tConfig = list_of_all_the_lines[0].split(" ")
    rowNum = int(tConfig[0])
    colNum = int(tConfig[1])
    configs = list_of_all_the_lines[1].split(',')
    templates = []
    for config in configs:
        cs = config.split(' ')
        cs0 = int(cs[0])
        cs1 = int(cs[1])
        cs2 = int(cs[2])
        template = Template(cs0 - 1, cs1 - 1, cs2, allChars[cs0 - 1:cs1])
        # print(allChars[cs0 - 1:cs1])
        templates.append(template)
    # detectRowNum = int(allChars[0][2])
    # detectColNum = int(allChars[0][3])
    # template = allChars[1:]
    return rowNum, colNum, templates


def initOutput(filename):
    path = './output/' + filename
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
    return path + '/'


def getFilePath(filename, imagename):
    return initOutput(filename) + imagename


#
#        ---- x2,y2
#       |    |
#  x1,y1 ----
# 原点在左下角
def writeBoxFile(boxInfo, filename, imgs, blockLineSize):
    '''将模板数据很检测到的位置信息写入文件box'''
    print('imgsize     ', len(imgs), boxInfo[0][0].val)
    totalHeight = 0
    for k in range(0, len(imgs)):
        imgHeight = imgs[k].shape[0]
        output = open(getFilePath(filename, 'eng.' + filename + '.exp{0}.box'.format(k + 1)),
                      'w')
        totalHeight = totalHeight + imgHeight
        for i in range(blockLineSize * k, min(blockLineSize * (k + 1), len(boxInfo))):  # 行
            for j in range(0, len(boxInfo[i])):  # 列
                box = boxInfo[i][j]
                # block中的左上角坐标 原点是block左上角
                xsrc = box.x
                ysrc = box.y - totalHeight + imgHeight
                # block中左下角和右上角坐标， 原点是block左下角
                x1 = xsrc
                y1 = imgHeight - ysrc - box.h
                x2 = xsrc + box.w
                y2 = imgHeight - ysrc
                val = box.val
                if box is not None and box != 0:
                    output.write(
                        val + " " + str(x1) + " " + str(y1) + " " + str(
                            x2) + " " + str(y2) + " 0\n")
                    if j == len(boxInfo[i]) - 1:
                        # 每行最后一个
                        output.write(
                            "\t" + " " + str(x2) + " " + str(y2) + " " + str(
                                x2 + 1) + " " + str(y2 + 1) + " 0\n")
                    else:
                        # 每个单词之间的空格
                        nextbox = boxInfo[i][j + 1]
                        if next is not None and nextbox != 0:
                            output.write(
                                " " + " " + str(x2 + 1) + " " + str(y1) + " " + str(
                                    nextbox.x) + " " + str(y2) + " 0\n")

        output.close()
    pass


def writeCharImg(boxInfo, filename, image):
    '''将模板数据很检测到的图片存储'''
    output = open(getFilePath(filename + '/chars', 'map_file.txt'), 'w')
    index = 0
    for i in range(0, len(boxInfo)):  # 行
        for j in range(0, len(boxInfo[i])):  # 列
            box = boxInfo[i][j]
            if box is not None and box != 0:
                char_img = image[box.y:box.y + box.h, box.x:box.x + box.w]
                cv.imwrite(getFilePath(filename + '/chars', str(index) + '.png'), char_img)
                output.write(
                    str(index) + " " + box.val + "\n")
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


def split(img, partNum):
    imgs = []
    w = img.shape[1]
    h = img.shape[0]
    perh = h / partNum
    for i in range(0, partNum):
        imgs.append(img[perh * i:perh * (i + 1), 0:w])
    return imgs


def doIntercept(filename, basePath, method, imgBlockLineSize):
    # 读取模板文件
    rowNum, colNum, templates = readTemplate()

    img = cv.imread(basePath + '/' + filename + '.tif', 1)  # 0表示灰度
    print(img.shape[0], img.shape[1], img.shape[2])
    maxWidth = 1500
    if img.shape[1] > maxWidth:  # 缩小图片尺寸 保证宽小于1000
        img = cv.resize(img, (maxWidth, int(img.shape[0] * maxWidth / img.shape[1])))

    img_src = img.copy()
    img_dc = img.copy()

    img = cv.GaussianBlur(img, (11, 11), 0)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    outerBox = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 5, 2)
    bw = cv.bitwise_not(outerBox)
    # 膨胀 ############
    # 构造一个5×5的结构元素
    # print(int(img.shape[1] * 0.015))
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
    print('cha ' + str(cha))
    # cha = 28
    bound = [boundRect[0] + cha, boundRect[1] + cha, boundRect[2] - cha * 2, boundRect[3] - cha * 2]
    # cv.imshow('image2', img_dc)
    # cv.imwrite(getFilePath(filename, 'img_dc.png'), img_dc)
    # cv.waitKey(0)
    # cv.destroyAllWindows()
    # 分割每个字符，计算box###########

    rowHeight = bound[3] / rowNum

    bw_fine_result = bw.copy()
    bw_fine_result[:] = 255
    boxTable = []
    # [[0 for i in range(colNum)] for j in range(rowNum)]
    img_inner = img_src[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2], :].copy()
    bw_fine_inner_result = bw_fine_result[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2]]
    bw_inner_src = outerBox[bound[1]:bound[1] + bound[3], bound[0]:bound[0] + bound[2]]
    cv.imwrite(getFilePath(filename, 'bw_inner_src.png'), bw_inner_src)

    for tpl in templates:
        rowst = tpl.rowst
        rowed = tpl.rowed
        colnum = tpl.col
        colWidth = bound[2] / colnum
        template = tpl.content
        for j in range(rowst, rowed + 1):
            boxline = []
            for i in range(0, colnum):
                # roi 先y轴再x轴
                y = bound[1] + j * rowHeight
                x = bound[0] + i * colWidth
                roi = erode[y:y + rowHeight,
                      x:x + colWidth]
                # bw_fine_result[y:y + rowHeight, x:x + colWidth] = outerBox[y:y + rowHeight,
                #                                                  x:x + colWidth]
                # img_inner = cv.rectangle(img_inner, (x - bound[0], y - bound[1]),
                #                          (x - bound[0] + colWidth, y - bound[1] + rowHeight), (255, 0, 0), 1)
                imInner, contoursInner, hierarchyInner = cv.findContours(roi, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                # img_dc_inner = cv.drawContours(roi_rgb, contoursInner, 0, (0, 255, 0), 1)
                if i < len(template[j - rowst]) and len(contoursInner) > 0:
                    val = template[j - rowst][i]
                    # print(val, j, rowst, i)
                    maxAreaI = findMaxAreaContours(contoursInner)
                    boundRectInner = cv.boundingRect(contoursInner[maxAreaI])
                    node = Node(x + boundRectInner[0] - bound[0],
                                y + boundRectInner[1] - bound[1],
                                boundRectInner[2],
                                boundRectInner[3], val)
                    img_inner = cv.rectangle(img_inner, (node.x, node.y),
                                             (node.x + node.w, node.y + node.h),
                                             (0, 255, 0), 1)
                    bw_fine_inner_result[node.y:node.y + node.h, node.x:node.x + node.w] = bw_inner_src[
                                                                                           node.y:node.y + node.h,
                                                                                           node.x:node.x + node.w]
                    boxline.append(node)
            boxTable.append(boxline)
        if method == 0:
            # break
            pass
    # cv.imwrite(getFilePath(filename, 'empty.png'), bw_fine_result)
    # print(boxTable)
    cv.imwrite(getFilePath(filename, 'result.png'), img_inner)
    cv.imwrite(getFilePath(filename, 'result_for_box.tif'), bw_fine_inner_result)
    # ################################
    # exit(0)
    parNum = 1
    if method == 0:
        # 输出chars字体所需图片和map文件
        boxTableFont = boxTable[0:templates[0].rowed + 1]
        writeCharImg(boxTableFont, filename, bw_fine_inner_result)
        # boxTable = boxTable[templates[0].rowed + 1:]
    # 输出box文件
    # 每3行一组分隔
    lastTplRow = templates[len(templates) - 1].rowed + 1
    print('lastTplRow', lastTplRow, imgBlockLineSize)
    parNum = lastTplRow / imgBlockLineSize
    if lastTplRow % imgBlockLineSize != 0:
        parNum += 1
    # 只取有用部分
    minusH = bw_fine_inner_result.shape[0] - bw_fine_inner_result.shape[0] * lastTplRow / rowNum

    bw_fine_inner_result = bw_fine_inner_result[0:bw_fine_inner_result.shape[0] - minusH, :]
    cv.imwrite(getFilePath(filename, 'bw_fine_inner_result.png'), bw_fine_inner_result)
    imgs = split(bw_fine_inner_result, parNum)
    firstPartNum = (templates[0].rowed + 1) / imgBlockLineSize
    if templates[0].rowed % imgBlockLineSize != 0:
        firstPartNum += 1
    for i in range(0, len(imgs)):
        cv.imwrite(getFilePath(filename, 'eng.{0}.exp{1}.tif'.format(filename, i + 1)), imgs[i])
    writeBoxFile(boxTable, filename, imgs, imgBlockLineSize)
    return parNum, firstPartNum
    # cv.waitKey(0)
    # cv.destroyAllWindows()
