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
from geom import *

class Page(object):
    def __init__(self, landscape = False, w = 210.0, h = 297.0, dpi = 72.0):
        self.DPI = dpi  # default dpi
        if not landscape:
            self.Size_mm = (w, h) # (width, height) in mm
        else:
            self.Size_mm = (h, w)
        self.Size = (self.Size_mm[0]/25.4 * self.DPI, self.Size_mm[1]/25.4 * self.DPI) # size in dots
        self._mag = 72.0/self.DPI;
        self.Margins = (15,)*4 # 15 mm
        txs = (self.Size[0] - self.Margins[1] - self.Margins[3], 
               self.Size[1] - self.Margins[0] - self.Margins[2])
        self.Text_rect = (self.Margins[1], self.Margins[0], txs[0], txs[1])

class PDFPage(Page):
    def __init__(self, filename, landscape = False, w = 210.0, h = 297.0, dpi = 72.0):
        super(PDFPage,self).__init__(landscape, w, h, dpi)
        if not landscape:
            self.Surface = cairo.PDFSurface (filename, self.Size[0]*self._mag, self.Size[1]*self._mag)
        else:
            self.Surface = cairo.PDFSurface (filename, self.Size[1]*self._mag, self.Size[0]*self._mag)
        self.cr = cairo.Context (self.Surface)
        self.cr.scale (self._mag, self._mag) # Normalizing the canvas
        if landscape:
            self.cr.translate(0,self.Size[0])
            self.cr.rotate(-math.pi/2)
            
def default_width(cr, factor = 1.0):
    return max(cr.device_to_user_distance(0.1*factor, 0.1*factor))

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
    fx, fy = thickness
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

def draw_box(cr, rect, stroke_rgba = (), fill_rgba = (), width_scale = 1.0, shadow = None):
    if (width_scale <= 0): return
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
        cr.set_line_width(default_width(cr, width_scale))
    cr.stroke()

def draw_str(cr, text, rect, stretch = -1, stroke_rgba = (), align = (2,0), bbox = False,
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
    
    cr.set_line_width(default_width(cr))
    cr.translate(px,py)
    cr.scale(*crs)
    if shadow is not None:
        cr.set_source_rgba(0, 0, 0, 0.5)
        u1, v1 = cr.user_to_device(0, 0)
        u1 += shadow[0]; v1 += shadow[1]
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
