#!/usr/local/bin/fontforge
# file test.py

import fontforge

font = fontforge.font()
family_name = "tesserthand"
style_name = "pw"
font.familyname = family_name
font.fullname = family_name + "-" + style_name
font.fontname = family_name + "-" + style_name
arr = ['F', 'O', 'P'];
for i in range(0, 3):
    glyph = font.createMappedChar(arr[i])
    glyph.importOutlines("/Users/wayne/Work/handwriting/pyhand/output/{0}.svg".format(arr[i]))
font.generate(font.fontname + '.ttf')
# or glyph.importOutlines("~/guitar.svg");
# or glyph.importOutlines("./guitar.svg");
# or glyph.importOutlines("guitar.svg");
