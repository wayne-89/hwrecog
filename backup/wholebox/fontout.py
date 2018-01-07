#!/usr/local/bin/fontforge
# coding=utf-8
# file test.py

import fontforge
import os


def convert2pbm(filepath):
    for filename in os.listdir(filepath):
        if filename.endswith('.png'):
            fileRealName = filename.split('.')[0]
            output = os.system(
                "convert {0}/{1} {0}/converted/{2}.pbm".format(filepath, filename, fileRealName))
    # output = os.system(
    #     "convert {0}/*.png -set filename:f '%t' '{0}/converted/%[filename:f].pbm'".format(filepath))


def convert2svg(filepath):
    for filename in os.listdir(filepath + "/converted"):
        if filename.endswith('.pbm'):
            fileRealName = filename.split('.')[0]
            cmd = "potrace -s {0}/converted/{1}.pbm -o {0}/converted/{1}.svg".format(filepath,
                                                                                     fileRealName)
            os.system(cmd)


def generate(filepath, name, mapFile, output):
    convertedPath = filepath + "/converted"
    isExists = os.path.exists(convertedPath)
    if not isExists:
        os.makedirs(convertedPath)

    convert2pbm(filepath)
    convert2svg(filepath)
    charMap = {}
    file = open(filepath + '/' + mapFile)
    list_of_all_the_lines = file.read().splitlines()
    # 文件名到字符的映射关系
    for line in list_of_all_the_lines:
        chars = line.split(" ")
        charMap[chars[0]] = chars[1]
    #

    font = fontforge.font()
    family_name = "tesseracthand"
    style_name = name
    font.familyname = family_name
    font.fullname = family_name + "-" + style_name
    font.fontname = family_name + "-" + style_name
    for filename in os.listdir(filepath):
        if filename.endswith('.png'):
            fileRealName = filename.split('.')[0]
            char = charMap[fileRealName]
            glyph = font.createMappedChar(char)
            glyph.importOutlines("{0}/converted/{1}.svg".format(filepath, fileRealName))
    font.generate(output + '/tesseracthand.ttf')
    return True
# generate("/Users/wayne/Work/handwriting/pyhand/output", 'pwpw', "map_file.txt")
