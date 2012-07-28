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

def draw_day_cell(cr, rect, day_of_month, header, footer, style, geom):
    x, y, w, h = rect
    draw_box(cr, rect, style.frame, style.bg, style.frame_thickness)
    R = rect_rel_scale(rect, geom.num_size[0], geom.num_size[1])
    draw_str(cr, text =day_of_month, rect = R, stretch = -1, stroke_rgba = style.fg, align = 2,
             font = style.font, measure = "55")
    if header:
        R = rect_rel_scale(rect, geom.header_size[0], geom.header_size[1], 0, -1.0+geom.header_align)
        draw_str(cr, text = header, rect = R, stretch = -1, stroke_rgba = style.header, align = 2,
             font = style.header_font)
    if footer:
        R = rect_rel_scale(rect, geom.footer_size[0], geom.footer_size[1], 0, 1.0-geom.footer_align)
        draw_str(cr, text = footer, rect = R, stretch = -1, stroke_rgba = style.footer, align = 2,
             font = style.footer_font)

def draw_month(cr, rect, month, year, theme, box_shadow = 0):
    S,G = theme
    apply_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

    cal = calendar.monthrange(year, month)
    day = cal[0]
    dom = -day + 1;
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
    grid = GLayout(rect_from_origin(rect), 7, 7)
    # 61.8% - 38.2% split (golden)
    R_mb, R_db = rect_vsplit(grid.item_span(1, 7, 0, 0), 0.618)  # month name bar, day name bar
    R_dnc = HLayout(R_db, 7) # day name cells = 1/7-th of day name bar
    for col in range(7):
        R = R_dnc.item(col)
        draw_box(cr, rect = R, stroke_rgba = S.dom.frame,
                 fill_rgba = S.dom.bg if col < 5 else S.dom_weekend.bg,
                 width_scale = S.dow.frame_thickness)
        R_text = rect_rel_scale(R, 1, 0.5)
        draw_str(cr, text = calendar.day_name[col], rect = R_text, stretch = -1, stroke_rgba = S.dow.fg,
                 align = 2, font = S.dow.font, measure = wmeasure)
    for row in range(6):
        for col in range(7):
            day_style = S.dom_weekend if col >= 5 else S.dom
            R = grid.item(row + 1, col)
            if dom > 0 and dom <= cal[1]:
                draw_day_cell(cr, rect = R, day_of_month = str(dom), header = None, footer = None,
                              style = day_style, geom = G.dom)
            else:
                draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                         width_scale = day_style.frame_thickness)
            dom += 1
            
    mcolor = S.month.color_map[month]
    mcolor_fg = color_auto_fg(mcolor)
    draw_box(cr, rect = rect_from_origin(rect), stroke_rgba = S.month.frame, fill_rgba = (),
             width_scale = 2, shadow = box_shadow)
    draw_box(cr, rect = R_mb, stroke_rgba = S.month.frame, fill_rgba = mcolor)
    R_text = rect_rel_scale(R_mb, 1, 0.5)
    draw_str(cr, text = calendar.month_name[month], rect = R_text, stretch = -1, stroke_rgba = mcolor_fg,
             align = 2, font = S.month.font, measure = mmeasure, shadow = S.month.text_shadow)
    cr.restore()
        
