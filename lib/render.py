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
#      calendar drawing routines          #
#                                         #
# *****************************************

import math
import calendar
import random
from xcairo import *
from geom import *

# TODO: replace rects with rect_rel_scale()
def draw_day_cell(cr, rect, day_of_month, header, footer, style, G):
    x, y, w, h = rect
    draw_box(cr, rect, style.frame, style.bg, style.frame_thickness)
    R = rect_rel_scale(rect, G.num_size[0], G.num_size[1])
    draw_str(cr, day_of_month, R, -1, style.fg, 2, 
             font = style.font, measure = "55")
    if header:
        R = (x + (1 - G.header_size[0])*w/2, y + G.top_margin*h,
             w*G.header_size[0], h*G.header_size[1])
        draw_str(cr, header, R, -1, style.header, 2, font = style.header_font)
    if footer:
        R = (x + (1 - G.footer_size[0])*w/2, y + (1 - G.bottom_margin - G.footer_size[1])*h,
             w*G.footer_size[0], h*G.footer_size[1])
        draw_str(cr, footer, R, -1, style.footer, 2, font = style.footer_font)

def draw_day_page(cr, rect, day_of_month, header, footer, fill = (1,1,1), stroke = (0,0,0)):
    x, y, w, h = rect
    draw_box(cr, rect, (0,0,0), fill)
    draw_str(cr, day_of_month, (x + w*.382/2, y + h*.382/2, w*.618, h*.618), 3, stroke)
    draw_str(cr, header, (x +0.1*w, y + 0.05*h, w*0.8, 0.1*h), -1, (0,0,0), 2)
    draw_str(cr, footer, (x +0.1*w, y + 0.85*h, w*0.8, 0.1*h), -1, (0,0,0), 2)

# TODO: implement GEOMETRY, STYLE, DATA SOURCES...
# TODO: use named options...
def draw_month(cr, rect, month, year, style, geom, box_shadow = 0):
    x, y, w, h = rect
    cw = w/7.0;
    ch = h/7.0;
    cr.save()
    cr.translate(x,y)

    cr.translate(w/2, h/2)
    cr.translate(w*(random.random() - 0.5)*geom.month.sloppy_dx,
                 h*(random.random() - 0.5)*geom.month.sloppy_dy)
    cr.rotate((random.random() - 0.5)*geom.month.sloppy_rot)
    cr.translate(-w/2.0, -h/2.0)

    cal = calendar.monthrange(year, month)
    day = cal[0]
    dom = -day + 1;
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
    for col in range(7):
        R = (col*cw, ch*3.0/5, cw, ch*2.0/5)
        draw_box(cr, R, style.dom.frame, 
                 style.dom.bg if col < 5 else style.dom_weekend.bg, style.dow.frame_thickness)
        R = (col*cw, ch*3.0/5 + ch*2.0/5*1.0/4, cw, ch*2.0/5*1/2)
        draw_str(cr, calendar.day_name[col], R, -1, style.dow.fg, 2, 
                 font = style.dow.font, measure = wmeasure)
    # TODO: use grid layout
    for row in range(6):
        for col in range(7):
            day_style = style.dom_weekend if col >= 5 else style.dom
            R = (col*cw, (row + 1)*ch, cw, ch)
            if dom > 0 and dom <= cal[1]:
                draw_day_cell(cr, R, str(dom), '', '', day_style, geom.dom)
            else:
                draw_box(cr, R, day_style.frame, day_style.bg, day_style.frame_thickness)
            dom += 1
            
    mcolor = style.month.color_map[month]
    mcolor_fg = color_auto_fg(mcolor)
    draw_box(cr, (0, 0, w, h), style.month.frame, (), 2, box_shadow)
    draw_box(cr, (0, 0, w, ch*3.0/5), style.month.frame, mcolor)
    R = (0, ch*3.0/5*1/4, w, ch*3.0/5*1/2)
    draw_str(cr, calendar.month_name[month], R, -1, mcolor_fg, 2, False,
             style.month.font, measure=mmeasure, shadow=style.month.text_shadow)
    cr.restore()
        