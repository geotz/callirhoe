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

# *****************************************
#                                         #
#      general-purpose drawing routines   #
#      higher-level CAIRO routines        #
#                                         #
# *****************************************

import cairo
import math
import random
from os.path import splitext
from geom import *

XDPI = 72.0
ISOPAGE = map(lambda x: int(210*math.sqrt(2)**x+0.5), range(5,-6,-1))

def page_spec(spec = None):
    if not spec:
        return (ISOPAGE[5], ISOPAGE[4])
    if len(spec) == 2 and spec[0].lower() == 'a':
        k = int(spec[1])
        return (ISOPAGE[k+1], ISOPAGE[k])
    if len(spec) == 3 and spec[0].lower() == 'a' and spec[2].lower() == 'w':
        k = int(spec[1])
        return (ISOPAGE[k], ISOPAGE[k+1])
    if ':' in spec:
        s = spec.split(':')
        w, h = float(s[0]), float(s[1])
        if w < 0: w = dots_to_mm(-w)
        if h < 0: h = dots_to_mm(-h)
        return (w,h)

def mm_to_dots(mm):
    return mm/25.4 * XDPI

def dots_to_mm(dots):
    return dots*25.4/XDPI

class Page(object):
    def __init__(self, landscape, w, h, b, raster):
        if not landscape:
            self.Size_mm = (w, h) # (width, height) in mm
        else:
            self.Size_mm = (h, w)
        self.landscape = landscape
        self.Size = (mm_to_dots(self.Size_mm[0]), mm_to_dots(self.Size_mm[1])) # size in dots/pixels
        self.raster = raster
        self.Margins = (mm_to_dots(b),)*4
        txs = (self.Size[0] - self.Margins[1] - self.Margins[3], 
               self.Size[1] - self.Margins[0] - self.Margins[2])
        self.Text_rect = (self.Margins[1], self.Margins[0], txs[0], txs[1])
        
class InvalidFormat(Exception): pass
        
class PageWriter(Page):
    PDF = 0
    PNG = 1
    def __init__(self, filename, landscape = False, pagespec = None, b = 0.0, keep_transparency = True):
        self.base,self.ext = splitext(filename)
        self.filename = filename
        self.curpage = 1
        if self.ext.lower() == ".pdf": self.format = PageWriter.PDF
        elif self.ext.lower() == ".png": self.format = PageWriter.PNG
        else:
            raise InvalidFormat(self.ext)
        self.keep_transparency = keep_transparency
        if keep_transparency:
            self.img_format = cairo.FORMAT_ARGB32
        else:
            self.img_format = cairo.FORMAT_RGB24
        w, h = page_spec(pagespec)
        if landscape and self.format == PageWriter.PNG:
            w, h = h, w
            landscape = False
        super(PageWriter,self).__init__(landscape, w, h, b, self.format == PageWriter.PNG)
        self.setup_surface_and_context()
            
    def setup_surface_and_context(self):
        if not self.landscape:
            if self.format == PageWriter.PDF:
                self.Surface = cairo.PDFSurface(self.filename, self.Size[0], self.Size[1])
            else:
                self.Surface = cairo.ImageSurface(self.img_format, int(self.Size[0]), int(self.Size[1]))
        else:
            if self.format == PageWriter.PDF:
                self.Surface = cairo.PDFSurface(self.filename, self.Size[1], self.Size[0])
            else:
                self.Surface = cairo.ImageSurface(self.img_format, int(self.Size[1]), int(self.Size[0]))
                
        self.cr = cairo.Context(self.Surface)
        if self.landscape:
            self.cr.translate(0,self.Size[0])
            self.cr.rotate(-math.pi/2)
        if not self.keep_transparency:
            self.cr.set_source_rgb(1,1,1)
            self.cr.move_to(0,0)
            self.cr.line_to(0,int(self.Size[1]))
            self.cr.line_to(int(self.Size[0]),int(self.Size[1]))
            self.cr.line_to(int(self.Size[0]),0)
            self.cr.close_path()
            self.cr.fill()
        
    def end_page(self):
        if self.format == PageWriter.PNG:
            outfile = self.filename if self.curpage < 2 else self.base + "%02d" % (self.curpage) + self.ext 
            self.Surface.write_to_png(outfile)
            
    def new_page(self):
        if self.format == PageWriter.PDF:
            self.cr.show_page()
        else:
            self.curpage += 1
            self.setup_surface_and_context()

            
def set_color(cr, rgba):
    if len(rgba) == 3:
        cr.set_source_rgb(*rgba)
    else:
        cr.set_source_rgba(*rgba)

def extract_font_name(f):
    return f if type(f) is str else f[0]

def apply_rect(cr, rect, sdx = 0.0, sdy = 0.0, srot = 0.0):
    x, y, w, h = rect
    cr.save()
    cr.translate(x,y)
    if sdx != 0.0 or sdy != 0.0 or srot != 0.0:
        cr.translate(w/2, h/2)
        cr.translate(w*(random.random() - 0.5)*sdx, h*(random.random() - 0.5)*sdy)
        cr.rotate((random.random() - 0.5)*srot)
        cr.translate(-w/2.0, -h/2.0)

def draw_shadow(cr, rect, thickness = None, shadow_color = (0,0,0,0.3)):
    if thickness is None: return
    fx = mm_to_dots(thickness[0])
    fy = mm_to_dots(thickness[1])
    x1, y1, x3, y3 = rect_to_abs(rect)
    x2, y2 = x1, y3
    x4, y4 = x3, y1
    u1, v1 = cr.user_to_device(x1,y1)
    u2, v2 = cr.user_to_device(x2,y2)
    u3, v3 = cr.user_to_device(x3,y3)
    u4, v4 = cr.user_to_device(x4,y4)
    u1 += fx; v1 += fy; u2 += fx; v2 += fy;
    u3 += fx; v3 += fy; u4 += fx; v4 += fy;
    x1, y1 = cr.device_to_user(u1, v1)
    x2, y2 = cr.device_to_user(u2, v2)
    x3, y3 = cr.device_to_user(u3, v3)
    x4, y4 = cr.device_to_user(u4, v4)
    cr.move_to(x1, y1)
    cr.line_to(x2, y2); cr.line_to(x3, y3); cr.line_to(x4, y4)
    set_color(cr, shadow_color)
    cr.close_path(); cr.fill();

def draw_box(cr, rect, stroke_rgba = None, fill_rgba = None, stroke_width = 1.0, shadow = None):
    if (stroke_width <= 0): return
    draw_shadow(cr, rect, shadow)
    x, y, w, h = rect
    cr.move_to(x, y)
    cr.rel_line_to(w, 0)
    cr.rel_line_to(0, h)
    cr.rel_line_to(-w, 0)
    cr.close_path()
    if fill_rgba:
        set_color(cr, fill_rgba)
        cr.fill_preserve()
    if stroke_rgba:
        set_color(cr, stroke_rgba)
        cr.set_line_width(stroke_width)
    cr.stroke()

def draw_str(cr, text, rect, stretch = -1, stroke_rgba = None, align = (2,0), bbox = False,
             font = "Times", measure = None, shadow = None):
    x, y, w, h = rect
    cr.save()
    slant = weight = 0
    if type(font) is str: fontname = font
    elif len(font) == 3: fontname, slant, weight = font
    elif len(font) == 2: fontname, slant = font
    elif len(font) == 1: fontname = font[0]
    cr.select_font_face(fontname, slant, weight)
    if measure is None: measure = text
    te = cr.text_extents(measure)
    mw, mh = te[2], te[3]
    ratio, tratio = w*1.0/h, mw*1.0/mh;
    xratio, yratio = mw*1.0/w, mh*1.0/h;
    if stretch < 0: stretch = 1 if xratio >= yratio else 2
    if stretch == 0: crs = (1,1)
    elif stretch == 1: crs = (1.0/xratio, 1.0/xratio)
    elif stretch == 2: crs = (1.0/yratio, 1.0/yratio)
    elif stretch == 3: crs = (1.0/xratio, 1.0/yratio)
    te = cr.text_extents(text)
    tw,th = te[2], te[3]
    tw *= crs[0]
    th *= crs[1]
    px, py = x, y + h
    if align[0] == 1: px += w - tw
    elif align[0] == 2: px += (w-tw)/2.0
    if align[1] == 1: py -= h - th
    elif align[1] == 2: py -= (h-th)/2.0
    
    cr.translate(px,py)
    cr.scale(*crs)
    if shadow is not None:
        sx = mm_to_dots(shadow[0])
        sy = mm_to_dots(shadow[1])
        cr.set_source_rgba(0, 0, 0, 0.5)
        u1, v1 = cr.user_to_device(0, 0)
        u1 += sx; v1 += sy
        x1, y1 = cr.device_to_user(u1, v1)
        cr.move_to(x1, y1)
        cr.show_text(text)
    cr.move_to(0, 0)
    if stroke_rgba: set_color(cr, stroke_rgba)
    cr.show_text(text)
    cr.restore()
    if bbox: 
        draw_box(cr, (x, y, w, h), stroke_rgba)
        #draw_box(cr, (x, y+h, mw*crs[0], -mh*crs[1]), stroke_rgba)
        draw_box(cr, (px, py, tw, -th), stroke_rgba)
