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

def weekrows_of_month(year, month):
    day,span = calendar.monthrange(year, month)
    if day == 0 and span == 28: return 4
    if day == 5 and span == 31: return 6
    if day == 6 and span >= 30: return 6
    return 5

def _draw_day_cell_short(cr, rect, day, header, footer, theme, show_day_name):
    S,G = theme
    x, y, w, h = rect
    day_of_month, day_of_week = day
    draw_box(cr, rect, S.frame, S.bg, S.frame_thickness)
    R = rect_rel_scale(rect, G.size[0], G.size[1], 0, -0.1)
    if show_day_name:
        Rdom, Rdow = rect_hsplit(R, *G.mw_split)
    else:
        Rdom = R
    draw_str(cr, text = str(day_of_month), rect = Rdom, stretch = -1, stroke_rgba = S.fg, align = 2,
             font = S.font, measure = "55")
    if show_day_name:
        draw_str(cr, text = calendar.day_name[day_of_week][0], rect = Rdow, stretch = -1, stroke_rgba = S.fg, align = 2,
                 font = S.font, measure = "55")
        
    if header:
        R = rect_rel_scale(rect, G.header_size[0], G.header_size[1], 0, -1.0 + G.header_align)
        draw_str(cr, text = header, rect = R, stretch = -1, stroke_rgba = S.header, align = 2,
             font = S.header_font)
    if footer:
        R = rect_rel_scale(rect, G.footer_size[0], G.footer_size[1], 0, 1.0 - G.footer_align)
        draw_str(cr, text = footer, rect = R, stretch = -1, stroke_rgba = S.footer, align = 2,
             font = S.footer_font)

def _draw_day_cell_long(cr, rect, day, header, footer, theme, show_day_name):
    S,G = theme
    x, y, w, h = rect
    day_of_month, day_of_week = day
    draw_box(cr, rect, S.frame, S.bg, S.frame_thickness)
    R1, Rhf = rect_hsplit(rect, *G.hf_hsplit)
    if show_day_name:
        R = rect_rel_scale(R1, G.size[2], G.size[3])
        Rdom, Rdow = rect_hsplit(R, *G.mw_split)
    else:
        Rdom = rect_rel_scale(R1, G.size[0], G.size[1])
    draw_str(cr, text = str(day_of_month), rect = Rdom, stretch = -1, stroke_rgba = S.fg, align = 2,
             font = S.font, measure = "55", bbox = False)
    if show_day_name:
        draw_str(cr, text = calendar.day_name[day_of_week][0], rect = Rdow, stretch = -1, stroke_rgba = S.fg, align = 2,
                 font = S.font, measure = "M", bbox = False)
    Rh, Rf = rect_vsplit(Rhf, *G.hf_vsplit)
    if header:
        draw_str(cr, text = header, rect = Rh, stretch = -1, stroke_rgba = S.header, align = 1,
             font = S.header_font, bbox = False)
    if footer:
        draw_str(cr, text = footer, rect = Rf, stretch = -1, stroke_rgba = S.footer, align = 1,
             font = S.footer_font, bbox = False)

def draw_day_cell(cr, rect, day, header, footer, theme, show_day_name):
    if rect_ratio(rect) > 2:
        _draw_day_cell_long(cr, rect, day, header, footer, theme, show_day_name)
    else:
        _draw_day_cell_short(cr, rect, day, header, footer, theme, show_day_name)
    

def _draw_month_matrix(cr, rect, month, year, theme):
    S,G = theme
    apply_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

    day, span = calendar.monthrange(year, month)
    weekrows = weekrows_of_month(year, month) if G.month.asymmetric else 6
    dom = -day + 1;
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
    grid = GLayout(rect_from_origin(rect), weekrows+1, 7)
    # 61.8% - 38.2% split (golden)
    R_mb, R_db = rect_vsplit(grid.item_span(1, 7, 0, 0), 0.618)  # month name bar, day name bar
    R_dnc = HLayout(R_db, 7) # day name cells = 1/7-th of day name bar
    
    if S.month.box_shadow:
        f = G.box_shadow_size
        shad = (f,-f) if G.landscape else (f,f)
        draw_shadow(cr, rect_from_origin(rect), shad)
    for col in range(7):
        R = R_dnc.item(col)
        draw_box(cr, rect = R, stroke_rgba = S.dom.frame,
                 fill_rgba = S.dom.bg if col < 5 else S.dom_weekend.bg,
                 width_scale = S.dow.frame_thickness)
        R_text = rect_rel_scale(R, 1, 0.5)
        draw_str(cr, text = calendar.day_name[col], rect = R_text, stretch = -1, stroke_rgba = S.dow.fg,
                 align = 2, font = S.dow.font, measure = wmeasure)
    for row in range(weekrows):
        for col in range(7):
            day_style = S.dom_weekend if col >= 5 else S.dom
            R = grid.item(row + 1, col)
            if dom > 0 and dom <= span:
                draw_day_cell(cr, rect = R, day = (dom, col), 
                              header = None, footer = None, theme = (day_style, G.dom), show_day_name = False)
            else:
                draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                         width_scale = day_style.frame_thickness)
            dom += 1
            
    mcolor = S.month.color_map[month]
    mcolor_fg = color_auto_fg(mcolor)
    draw_box(cr, rect = rect_from_origin(rect), stroke_rgba = S.month.frame, fill_rgba = (),
             width_scale = S.month.frame_thickness)
    draw_box(cr, rect = R_mb, stroke_rgba = S.month.frame, fill_rgba = mcolor)
    R_text = rect_rel_scale(R_mb, 1, 0.5)
    mshad = None
    if S.month.text_shadow:
        mshad = (0.5,-0.5) if G.landscape else (0.5,0.5)
    draw_str(cr, text = calendar.month_name[month], rect = R_text, stretch = -1, stroke_rgba = mcolor_fg,
             align = 2, font = S.month.font, measure = mmeasure, shadow = mshad)
    cr.restore()

def _draw_month_bar(cr, rect, month, year, theme):
    S,G = theme
    apply_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

    day, span = calendar.monthrange(year, month)
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
    rows = (span + 1) if G.month.asymmetric else 32 
    grid = VLayout(rect_from_origin(rect), rows)
    
    if S.month.box_shadow:
        f = G.box_shadow_size
        shad = (f,-f) if G.landscape else (f,f)
        draw_shadow(cr, rect_from_origin(rect), shad)
    for dom in range(1,rows):
        day_style = S.dom_weekend if day >= 5 and dom <= span else S.dom
        R = grid.item(dom)
        if dom <= span:
            draw_day_cell(cr, rect = R, day = (dom, day), 
                          header = None, footer = None, theme = (day_style, G.dom), show_day_name = True)
        else:
            draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                     width_scale = day_style.frame_thickness)
        day = (day + 1) % 7
        
    mcolor = S.month.color_map[month]
    mcolor_fg = color_auto_fg(mcolor)
    draw_box(cr, rect = rect_from_origin(rect), stroke_rgba = S.month.frame, fill_rgba = (),
             width_scale = S.month.frame_thickness)
    R_mb = grid.item(0)
    draw_box(cr, rect = R_mb, stroke_rgba = S.month.frame, fill_rgba = mcolor)
    R_text = rect_rel_scale(R_mb, 1, 0.5)
    mshad = None
    if S.month.text_shadow:
        mshad = (0.5,-0.5) if G.landscape else (0.5,0.5)
    draw_str(cr, text = calendar.month_name[month], rect = R_text, stretch = -1, stroke_rgba = mcolor_fg,
             align = 2, font = S.month.font, measure = mmeasure, shadow = mshad)
    cr.restore()

def draw_month(cr, rect, month, year, theme):
    if rect_ratio(rect) > 0.75:
        _draw_month_matrix(cr, rect, month, year, theme)
    else:
        _draw_month_bar(cr, rect, month, year, theme)
