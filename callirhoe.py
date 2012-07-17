#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012 George M. Tzoumas

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/

_version = "0.1"

import calendar
import sys
import time
import os.path
import optparse
import glob

from lib.xcairo import *
from lib.render import *

plugin_path = [ os.path.expanduser("~/.callirhoe"), sys.path[0] if sys.path[0] else "." ]

def available_files(parent, dir, fmatch = ""):
    good = False
    res = []
    pattern = parent + "/" + dir + "/*.py"
    # TODO: improve matching with __init__ when lang known
    for x in glob.glob(pattern):
        basex = os.path.basename(x)
        if basex == "__init__.py": good = True
        else: 
            base = os.path.splitext(basex)[0]
            if base and ((not fmatch) or (fmatch == base)): res.append((base,parent))
    return res if good else []

# cat = lang   (category)
# longcat = language
# longcat2 = languages
# listopt = --list-lang
# preset = "EN"
def import_plugin(cat, longcat, longcat2, listopt, preset):
    try:
        found = available_files(plugin_path[0], cat, preset) + available_files(plugin_path[1], cat, preset)
        if len(found) == 0: raise ImportError
        old = sys.path[0];
        sys.path[0] = found[0][1]
        m = __import__("%s.%s" % (cat,preset), globals(), locals(), [ "*" ])
        sys.path[0] = old
        return m
    except ImportError:
        print >> sys.stderr, "%s definition `%s' not found, use %s to see available %s" % (longcat,preset,listopt,longcat2)
        sys.exit(1)

parser = optparse.OptionParser(usage="usage: %prog [options] FILE", 
       description="High quality calendar rendering with vector graphics.\n"
       "By default, a pdf calendar of the current year will be written to FILE. Program version: " + _version)
parser.add_option("-y", "--year",  dest="year", type="int", default=-1,
                help="select YEAR instead of current one")
parser.add_option("-l", "--lang",  dest="lang", default="EN",
                help="choose language [EN]")
parser.add_option("-s", "--style",  dest="style", default="default",
                help="choose style [default]")
parser.add_option("-g", "--geometry",  dest="geom", default="default",
                help="choose geometry [default]")
parser.add_option("--landscape", action="store_true", dest="landscape", default=False,
                help="landscape mode")
parser.add_option("--list-languages", action="store_true", dest="list_languages", default=False,
                help="list available languages")
parser.add_option("--list-styles", action="store_true", dest="list_styles", default=False,
                help="list available styles")
parser.add_option("--list-geometries", action="store_true", dest="list_geometries", default=False,
                help="list available geometries")
parser.add_option("--lang-var", action="append", dest="lang_assign",
                help="modify a language variable")
parser.add_option("--style-var", action="append", dest="style_assign",
                help="modify a style variable, e.g. dom.frame_thickness=0")
parser.add_option("--geom-var", action="append", dest="geom_assign",
                help="modify a geometry variable")

#for x in sys.argv:
#    if x[0] == '-' and not parser.has_option(x):
#        print "possibly bad option", x
# ./callirhoe --lang fr year=2010 months=1-6 foo.pdf
        
(options,args) = parser.parse_args()

def plugin_list(cat):
    return available_files(plugin_path[0], cat) + available_files(plugin_path[1], cat)
if options.list_languages:
    for x in plugin_list("lang"): print x[0],
    print
if options.list_styles:
    for x in plugin_list("style"): print x[0],
    print
if options.list_geometries:
    for x in plugin_list("geom"): print x[0],
    print
if options.list_languages or options.list_styles or options.list_geometries: sys.exit(0)    

if len(args)==0:
    parser.print_help()
    sys.exit(0)

cal_lang = import_plugin("lang", "language", "languages", "--list-languages", options.lang)
cal_style = import_plugin("style", "style", "styles", "--list-styles", options.style)
cal_geom = import_plugin("geom", "geometry", "geometries", "--list-geometries", options.geom)

if options.lang_assign:
    for x in options.lang_assign: exec "cal_lang.%s" % x
if options.style_assign:
    for x in options.style_assign: exec "cal_style.%s" % x
if options.geom_assign:
    for x in options.geom_assign: exec "cal_geom.%s" % x

calendar.month_name = cal_lang.month_name
calendar.day_name = cal_lang.day_name

def get_orthodox_easter(y):
    y1, y2, y3 = y - y//4 * 4, y - y//7 * 7, y - y//19 * 19
    a = 19*y3 + 15
    y4 = a - a//30 * 30
    b = 2*y1 + 4*y2 + 6*(y4 + 1)
    y5 = b - b/7 * 7
    r = 1 + 3 + y4 + y5;
    return (5, r - 30) if r > 30 else (4,r)

year = options.year if options.year >= 0 else time.localtime()[0]

p = PDFPage(args[0], options.landscape)

R0,R1 = rect_vsplit(p.Text_rect, 0.05)
Rcal,Rc = rect_vsplit(R1,0.97)
if options.landscape:
    rows,cols = 3,4
else:
    rows,cols = 4,3
foo = GLayout(Rcal, rows, cols, pad = (p.Text_rect[2]*0.02,)*4)
shad = p.Size[0]*0.01 if cal_style.month.box_shadow else 0
for i in range(min(foo.count(),12),0,-1):
    draw_month(p.cr, foo.item_seq(i-1), month=i, year=year, 
               style = cal_style, geom = cal_geom, box_shadow = shad)
#    render.draw_box(render.cr,*foo.item_seq(i))
#draw_str(p.cr, str(year), R0, stroke_rgba = (0,0,0,0.3), align=1)
draw_str(p.cr, str(year), R0, stroke_rgba = (0,0,0,0.3), align=2)
#draw_str(p.cr, str(year), R0, stroke_rgba = (0,0,0,0.3), align=3)
draw_str(p.cr, "created by Callirhoe ver.0.1 © 2012 GeoTz", Rc, stroke_rgba = (0,0,0,0.5), stretch=0, align=2, slant=cairo.FONT_SLANT_ITALIC)

#render.cr.move_to(render.Page.Text_pos[0],render.Page.Text_pos[1])
#render.cr.line_to(render.Page.Text_size[0]+render.Page.Text_pos[0], render.Page.Text_size[1]+render.Page.Text_pos[1])
#render.cr.stroke()

#draw_month(cr, *foo.item(2), m=9)

#bw, bh = 40,40
#draw_day_cell(cr, 30, 50, bw, bh, '24', 'Παραμονή Χριστουγ.', 'Ευγενία', default_style)
#draw_day_cell(cr, 30+bw, 50, bw, bh, '25', 'ΧΡΙΣΤΟΥΓΕΝΝΑ', 'Χρήστος, Χριστίνα', weekend_holiday_style)
#draw_day_cell(cr, 30+2*bw, 50, bw, bh, '26', '2η μέρα Χριστουγ.', 'Εμμανουήλ', weekend_style)
#draw_day_cell(cr, 30+3*bw, 50, bw, bh, '27', '', 'Στέφανος', default_style)
#draw_day_page(cr, 30+2*bw, 50, bw, bh, '26', 'Κυριακή', 'Δεκεμβρίου', [1,1,1], [.3,.3,.3])
