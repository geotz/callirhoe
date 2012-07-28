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

class Page(object):
    def __init__(self, landscape = False, w = 210.0, h = 297.0, dpi = 72.0):
        self.DPI = dpi  # default dpi
        if not landscape:
            self.Size_mm = (w, h) # (width, height) in mm
        else:
            self.Size_mm = (h, w)
        self.Size = (self.Size_mm[0]/25.4 * self.DPI, self.Size_mm[1]/25.4 * self.DPI) # size in dots
        self._mag = 72.0/self.DPI;
        self.Margins = (self.Size[1]*0.025, self.Size[0]*0.025, 
                        self.Size[1]*0.025, self.Size[0]*0.025) # top left bottom right
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

def draw_shadow(cr, rect, thickness, shadow_color = (0,0,0,0.3)):
    if thickness <= 0: return
    f = thickness
    x, y, w, h = rect
    cr.move_to(x + f, y + h)
    cr.rel_line_to(0, f); cr.rel_line_to(w, 0); cr.rel_line_to(0, -h)
    cr.rel_line_to(-f, 0); cr.rel_line_to(0, h - f); cr.rel_line_to(-w + f, 0);
    set_color(cr, shadow_color)
    cr.close_path(); cr.fill();

def draw_box(cr, rect, stroke_rgba = (), fill_rgba = (), width_scale = 1.0, shadow = 0):
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

def draw_str(cr, text, rect, stretch = -1, stroke_rgba = (), align = 0, bbox = False,
             font = "Times", measure = '', shadow = False):
    x, y, w, h = rect
    cr.save()
    slant = weight = 0
    if type(font) is str: fontname = font
    elif len(font) == 3: fontname, slant, weight = font
    elif len(font) == 2: fontname, slant = font
    elif len(font) == 1: fontname = font[0]
    cr.select_font_face(fontname, slant, weight)
    if not measure: measure = text
    te = cr.text_extents(measure)
    tw, th = te[2], te[3]
    cr.translate(x, y + h)
    ratio, tratio = w*1.0/h, tw*1.0/th;
    xratio, yratio = tw*1.0/w, th*1.0/h;
    if stretch < 0: stretch = 1 if xratio >= yratio else 2
    if stretch == 0: bbw, bbh = w, h;
    elif stretch == 1: bbw, bbh = tw, tw/ratio; cr.scale(1.0/xratio, 1.0/xratio)
    elif stretch == 2: bbw, bbh = th*ratio, th; cr.scale(1.0/yratio, 1.0/yratio)
    elif stretch == 3: bbw, bbh = tw, th; cr.scale(1.0/xratio, 1.0/yratio)
    te = cr.text_extents(text)
    tw,th = te[2], te[3]
    if align == 1: px, py = bbw - tw, 0
    elif align == 2: px, py = (bbw-tw)/2.0, 0
    else: px, py = 0, 0
    cr.set_line_width(default_width(cr))
    if shadow:
        cr.set_source_rgba(0, 0, 0, 0.5)
        cr.move_to(px + default_width(cr, 5), py + default_width(cr, 5))
        cr.show_text(text)
    cr.move_to(px, py)
    if stroke_rgba: set_color(cr, stroke_rgba)
    cr.show_text(text)
    if bbox: draw_box(cr, (0, 0, bbw, -bbh), stroke_rgba)
    cr.restore()
