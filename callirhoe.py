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
        print >> sys.stderr, "%s definition `%s' not found, use %s to see available %s" % (longcat,
                               preset,listopt,longcat2)
        sys.exit(1)

# TODO:
# prog [[MONTH1-MONTH2 | MONTH:SPAN] YEAR] FILE
parser = optparse.OptionParser(usage="usage: %prog [options] [YEAR [MONTH [SPAN]]] FILE", 
       description="High quality calendar rendering with vector graphics.\n"
       "By default, a pdf calendar of the current year will be written to FILE. Program version: " + _version)
parser.add_option("-l", "--lang",  dest="lang", default="EN",
                help="choose language [EN]")
parser.add_option("-t", "--template",  dest="template", default="tiles",
                help="choose template [tiles]")
parser.add_option("-s", "--style",  dest="style", default="default",
                help="choose style [default]")
parser.add_option("-g", "--geometry",  dest="geom", default="default",
                help="choose geometry [default]")
parser.add_option("--landscape", action="store_true", dest="landscape", default=False,
                help="landscape mode")
                
def add_list_option(parser, opt):
    parser.add_option("--list-%s" % opt, action="store_true", dest="list_%s" % opt, default=False,
                       help="list available %s" % opt)
for x in ["languages", "templates", "styles", "geometries"]:
    add_list_option(parser, x)

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
if options.list_templates:
    for x in plugin_list("templates"): print x[0],
    print
if (options.list_languages or options.list_styles or
    options.list_geometries or options.list_templates): sys.exit(0)    

if len(args)==0:
    parser.print_help()
    sys.exit(0)

Language = import_plugin("lang", "language", "languages", "--list-languages", options.lang)
Style = import_plugin("style", "style", "styles", "--list-styles", options.style)
Geometry = import_plugin("geom", "geometry", "geometries", "--list-geometries", options.geom)

if options.lang_assign:
    for x in options.lang_assign: exec "Language.%s" % x
if options.style_assign:
    for x in options.style_assign: exec "Style.%s" % x
if options.geom_assign:
    for x in options.geom_assign: exec "Geometry.%s" % x

calendar.month_name = Language.month_name
calendar.day_name = Language.day_name

def get_orthodox_easter(y):
    y1, y2, y3 = y - y//4 * 4, y - y//7 * 7, y - y//19 * 19
    a = 19*y3 + 15
    y4 = a - a//30 * 30
    b = 2*y1 + 4*y2 + 6*(y4 + 1)
    y5 = b - b/7 * 7
    r = 1 + 3 + y4 + y5;
    return (5, r - 30) if r > 30 else (4,r)

ac = 0
try:
    if len(args) > 1: Year = int(args[ac]); ac += 1
    else: Year = time.localtime()[0]
except ValueError as e:
    sys.exit("invalid year `" + args[ac] +"'")
try:
    if len(args) > 2: Month = int(args[ac]); ac += 1
    else: Month = 1
    if Month < 1: Month = time.localtime()[1]
    if Month > 12: ac -= 1; raise ValueError() # nasty!
except ValueError as e:
    sys.exit("invalid month `" + args[ac] +"'")
try:
    if len(args) > 3: MonthSpan = int(args[ac]); ac += 1
    else: MonthSpan = 12
    if MonthSpan < 1: ac -= 1; raise ValueError() # nasty!
except ValueError as e:
    sys.exit("invalid month span `" + args[ac] +"'")

print Year, Month, MonthSpan

# TODO: maybe add warning when last arg looks like an int
p = PDFPage(args[ac], options.landscape)


#1   1   1
#2   2   1
#3   3   1

#4   2   2
#5   3   2
#6   3   2
#7   4   2
#8   4   2

#9   3   3
#10  4   3
#11  4   3
#12  4   3
if MonthSpan < 4: cols = 1; rows = MonthSpan
elif MonthSpan < 9: cols = 2; rows = int(math.ceil(MonthSpan/2.0))
else: cols = 3; rows = int(math.ceil(MonthSpan/3.0))

# else x = floor(sqrt(span))... consider x*x, (x+1)*x, (x+1)*(x+1)

# TODO: allow /usr/bin/date -like formatting %x... 
# fix frame_thickness usage (add month. or use same everywhere)

R0,R1 = rect_vsplit(p.Text_rect, 0.05)
Rcal,Rc = rect_vsplit(R1,0.97)
if options.landscape: rows,cols = cols,rows
# TODO: wrap around years
foo = GLayout(Rcal, rows, cols, pad = (p.Text_rect[2]*0.02,)*4)
shad = p.Size[0]*0.01 if Style.month.box_shadow else 0
for i in range(min(foo.count(),MonthSpan),0,-1):
    draw_month(p.cr, foo.item_seq(i-1), month=i+Month-1, year=Year, 
               style = Style, geom = Geometry, box_shadow = shad)
draw_str(p.cr, str(Year), R0, stroke_rgba = (0,0,0,0.3), align=2)
draw_str(p.cr, "rendered by Callirhoe ver. %s" % _version, 
         Rc, stroke_rgba = (0,0,0,0.5), stretch=0, align=1, slant=cairo.FONT_SLANT_ITALIC)
