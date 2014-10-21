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

# ********************************************************************
#                                                                    #
""" general-purpose drawing routines & higher-level CAIRO routines """
#                                                                    #
# ********************************************************************

import cairo
import math
import random
from os.path import splitext
from geom import *

XDPI = 72.0
"""dots per inch of output device"""

# decreasing order
# [1188, 840, 594, 420, 297, 210, 148, 105, 74, 52, 37]
ISOPAGE = map(lambda x: int(210*math.sqrt(2)**x+0.5), range(5,-6,-1))
"""ISO page height list, index k for height of Ak paper"""

def page_spec(spec = None):
    """return tuple of page dimensions (width,height) in mm for I{spec}

    @param spec: paper type.
        Paper type can be an ISO paper type (a0..a9 or a0w..a9w) or of the
        form W:H; positive values correspond to W or H mm, negative values correspond to
        -W or -H pixels; 'w' suffix swaps width & height; None defaults to A4 paper

    @rtype: (int,int)
    """
    if not spec:
        return (ISOPAGE[5], ISOPAGE[4])
    if len(spec) == 2 and spec[0].lower() == 'a':
        k = int(spec[1])
        if k > 9: k = 9
        return (ISOPAGE[k+1], ISOPAGE[k])
    if len(spec) == 3 and spec[0].lower() == 'a' and spec[2].lower() == 'w':
        k = int(spec[1])
        if k > 9: k = 9
        return (ISOPAGE[k], ISOPAGE[k+1])
    if ':' in spec:
        s = spec.split(':')
        w, h = float(s[0]), float(s[1])
        if w < 0: w = dots_to_mm(-w)
        if h < 0: h = dots_to_mm(-h)
        return (w,h)

def mm_to_dots(mm):
    """convert millimeters to dots

    @rtype: float
    """
    return mm/25.4 * XDPI

def dots_to_mm(dots):
    """convert dots to millimeters

    @rtype: float
    """
    return dots*25.4/XDPI

class Page(object):
    """class holding Page properties

    @type Size_mm: tuple (width,height)
    @ivar Size_mm: page dimensions in mm
    @type landscape: bool
    @ivar landscape: landscape mode (for landscape, Size_mm will have swapped elements)
    @type Size: tuple (width,height)
    @ivar Size: page size in dots/pixels
    @type Margins: tuple (top,left,bottom,right)
    @ivar Margins: page margins in pixels
    @type Text_rect: tuple (x,y,w,h)
    @ivar Text_rect: text rectangle
    """
    def __init__(self, landscape, w, h, b, raster):
        """initialize Page properties object

        @type landscape: bool
        @param landscape: landscape mode
        @param w: page physical width in mm
        @param h: page physical height in mm, M{h>w}, even in landscape mode
        @param b: page border in mm (uniform)
        @type raster: bool
        @param raster: raster mode (not vector)
        """
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
        
class InvalidFormat(Exception):
    """exception thrown when an invalid output format is requested"""
    pass
        
class PageWriter(Page):
    """class to output multiple pages in raster (png) or vector (pdf) format


    @ivar base: out filename (without extension)
    @ivar ext: filename extension (with dot)
    @type curpage: int
    @ivar curpage: current page
    @ivar format: output format: L{PDF} or L{PNG}
    @type keep_transparency: bool
    @ivar keep_transparency: C{True} to use transparent instead of white fill color
    @ivar img_format: C{cairo.FORMAT_ARGB32} or C{cairo.FORMAT_RGB24} depending on
    L{keep_transparency}
    @ivar Surface: cairo surface (set by L{_setup_surface_and_context})
    @ivar cr: cairo context (set by L{_setup_surface_and_context})
    """

    PDF = 0
    PNG = 1
    def __init__(self, filename, pagespec = None, keep_transparency = True, landscape = False, b = 0.0):
        """initialize PageWriter object

        see also L{Page.__init__}
        @param filename: output filename (extension determines format PDF or PNG)
        @param pagespec: iso page spec, see L{page_spec}
        @param keep_transparency: see L{keep_transparency}
        """
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
        self._setup_surface_and_context()
            
    def _setup_surface_and_context(self):
        """setup cairo surface taking into account raster mode, transparency and landscape mode"""
        z = int(self.landscape)
        if self.format == PageWriter.PDF:
            self.Surface = cairo.PDFSurface(self.filename, self.Size[z], self.Size[1-z])
        else:
            self.Surface = cairo.ImageSurface(self.img_format, int(self.Size[z]), int(self.Size[1-z]))
                
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
        """in PNG mode, output a separate file for each page"""
        if self.format == PageWriter.PNG:
            outfile = self.filename if self.curpage < 2 else self.base + "%02d" % (self.curpage) + self.ext 
            self.Surface.write_to_png(outfile)
            
    def new_page(self):
        """setup next page"""
        if self.format == PageWriter.PDF:
            self.cr.show_page()
        else:
            self.curpage += 1
            self._setup_surface_and_context()

            
def set_color(cr, rgba):
    """set stroke color

    @param cr: cairo context
    @type rgba: tuple
    @param rgba: (r,g,b) or (r,g,b,a)
    """
    if len(rgba) == 3:
        cr.set_source_rgb(*rgba)
    else:
        cr.set_source_rgba(*rgba)

def extract_font_name(f):
    """extract the font name from a string or from a tuple (fontname, slant, weight)

    @rtype: str
    """
    return f if type(f) is str else f[0]

def make_sloppy_rect(cr, rect, sdx = 0.0, sdy = 0.0, srot = 0.0):
    """slightly rotate and translate a rect to give it a sloppy look

    @param cr: cairo context
    @param sdx: maximum x-offset, true offset will be uniformly distibuted
    @param sdy: maximum y-offset
    @param sdy: maximum rotation
    """
    x, y, w, h = rect
    cr.save()
    cr.translate(x,y)
    if sdx != 0.0 or sdy != 0.0 or srot != 0.0:
        cr.translate(w/2, h/2)
        cr.translate(w*(random.random() - 0.5)*sdx, h*(random.random() - 0.5)*sdy)
        cr.rotate((random.random() - 0.5)*srot)
        cr.translate(-w/2.0, -h/2.0)

def draw_shadow(cr, rect, thickness = None, shadow_color = (0,0,0,0.3)):
    """draw a shadow at the bottom-right corner of a rect

    @param cr: cairo context
    @param rect: tuple (x,y,w,h)
    @param thickness: if C{None} nothing is drawn
    @param shadow_color: shadow color
    """
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

def draw_line(cr, rect, stroke_rgba = None, stroke_width = 1.0):
    """draw a line from (x,y) to (x+w,y+h), where rect=(x,y,w,h)

    @param cr: cairo context
    @param rect: tuple (x,y,w,h)
    @param stroke_rgba: stroke color
    @param stroke_width: stroke width, if <= 0 nothing is drawn
    """
    if (stroke_width <= 0): return
    x, y, w, h = rect
    cr.move_to(x, y)
    cr.rel_line_to(w, h)
    cr.close_path()
    if stroke_rgba:
        set_color(cr, stroke_rgba)
        cr.set_line_width(stroke_width)
    cr.stroke()

def draw_box(cr, rect, stroke_rgba = None, fill_rgba = None, stroke_width = 1.0, shadow = None):
    """draw a box (rectangle) with optional shadow

    @param cr: cairo context
    @param rect: box rectangle as tuple (x,y,w,h)
    @param stroke_rgba: stroke color (set if not C{None})
    @param fill_rgba: fill color (set if not C{None})
    @param stroke_width: stroke width
    @param shadow: shadow thickness
    """
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

def draw_str(cr, text, rect, scaling = -1, stroke_rgba = None, align = (2,0), bbox = False,
             font = "Times", measure = None, shadow = None):
    """draw text

    @param cr: cairo context
    @param text: text string to be drawn
    @type scaling: int
    @param scaling: text scaling mode

        - -1: auto select x-scaling or y-scaling (whatever fills the rect)
        - 0: no scaling
        - 1: x-scaling, scale so that text fills rect horizontally, preserving ratio
        - 2: y-scaling, scale so that text fills rect vertically, preserving ratio
        - 3: xy-scaling, stretch so that text fills rect completely, does not preserve ratio

    @param stroke_rgba: stroke color
    @type align: tuple
    @param align: alignment mode as (int,int) tuple for horizontal/vertical alignment

        - 0: left/top alignment
        - 1: right/bottom alignment
        - 2: center/middle alignment

    @param bbox: draw text bounding box (for debugging)
    @param font: font name as string or (font,slant,weight) tuple
    @param measure: use this string for measurement instead of C{text}
    @param shadow: draw text shadow as tuple (dx,dy)
    """
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
    if mw < 5:
      mw = 5.
    if mh < 5:
      mh = 5.
    #ratio, tratio = w*1.0/h, mw*1.0/mh;
    xratio, yratio = mw*1.0/w, mh*1.0/h;
    if scaling < 0: scaling = 1 if xratio >= yratio else 2
    if scaling == 0: crs = (1,1)
    elif scaling == 1: crs = (1.0/xratio, 1.0/xratio)
    elif scaling == 2: crs = (1.0/yratio, 1.0/yratio)
    elif scaling == 3: crs = (1.0/xratio, 1.0/yratio)
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
