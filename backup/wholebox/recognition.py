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


def convert(filepath, name):
    os.system(
        'convert {0} ./recog/{1}/{1}.pbm'.format(filepath, name))
    os.system(
        'potrace -s ./recog/{0}/{0}.pbm -o ./recog/{0}/{0}.eps'.format(name))
    return os.system('convert ./recog/{0}/{0}.eps ./recog/{0}/{0}_final.png'.format(name))


def doIntercept(filepath):
    models = filepath.split('/')
    name = filepath.split('/')[len(models) - 1].split('.')[0]
    img = cv.imread(filepath, 1)  # 0表示灰度
    print(name)
    img = cv.GaussianBlur(img, (11, 11), 0)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    outerBox = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 5, 2)
    bw = outerBox  # cv.bitwise_and(outerBox)
    os.system('mkdir -p ./recog/{0}'.format(name))
    cv.imwrite('./recog/{0}/{0}_bw.tif'.format(name), bw)
    convert('./recog/{0}/{0}_bw.tif'.format(name), name)
    cmd = 'tesseract  --tessdata-dir ./lstm/result  ./recog/{0}/{0}_final.png {1}.out -l eng --oem 1 --psm 3'.format(
        name,
        filepath)
    print(cmd)
    os.system(cmd)
    return True
    # cv.waitKey(0)
    # cv.destroyAllWindows()


doIntercept('/Users/wayne/Documents/tesseract/test/lzx2.png')
