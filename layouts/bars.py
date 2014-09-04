# -*- coding: utf-8 -*-
#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012-2014 George M. Tzoumas

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

"""bars layout"""

from lib.xcairo import *
from lib.geom import *
import calendar
import optparse
import sys
from datetime import date, timedelta

import _base

parser = _base.get_parser(__name__)
parser.set_defaults(rows=2)

class CalendarRenderer(_base.CalendarRenderer):
    """bars layout class"""
    def _draw_month(self, cr, rect, month, year):
        S,G,L = self.Theme
        make_sloppy_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

        day, span = calendar.monthrange(year, month)
        mmeasure = 'A'*max(map(len,L.month_name))
        if self.options.month_with_year:
            mmeasure += 'A'*(len(str(year))+1)

        rows = 31 if G.month.symmetric else span 
        grid = VLayout(rect_from_origin(rect), 32) # title bar always symmetric
        dom_grid = VLayout(grid.item_span(31,1), rows)

        # draw box shadow    
        if S.month.box_shadow:
            f = S.month.box_shadow_size
            shad = (f,-f) if G.landscape else (f,f)
            draw_shadow(cr, rect_from_origin(rect), shad)
            
        # draw day cells
        for dom in range(1,rows+1):
            R = dom_grid.item(dom-1)
            if dom <= span:
                holiday_tuple = self.holiday_provider(year, month, dom, day)
                day_style = holiday_tuple[2]
                dcell = _base.DayCell(day = (dom, day), header = holiday_tuple[0], footer = holiday_tuple[1],
                                      theme = (day_style, G.dom, L), show_day_name = True)
                dcell.draw(cr, R, self.options.short_daycell_ratio)
            else:
                day_style = S.dom
                draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                         stroke_width = mm_to_dots(day_style.frame_thickness))
            day = (day + 1) % 7
            
        # draw month title (name)
        mcolor = S.month.color_map_bg[year%2][month]
        mcolor_fg = S.month.color_map_fg[year%2][month]
        R_mb = grid.item(0)
        draw_box(cr, rect = R_mb, stroke_rgba = S.month.frame, fill_rgba = mcolor,
                 stroke_width = mm_to_dots(S.month.frame_thickness)) # title box
        draw_box(cr, rect = rect_from_origin(rect), stroke_rgba = S.month.frame, fill_rgba = (),
                 stroke_width = mm_to_dots(S.month.frame_thickness)) # full box
        R_text = rect_rel_scale(R_mb, 1, 0.5)
        mshad = None
        if S.month.text_shadow:
            f = S.month.text_shadow_size
            mshad = (f,-f) if G.landscape else (f,f)
        title_str = L.month_name[month]
        if self.options.month_with_year: title_str += ' ' + str(year)
        draw_str(cr, text = title_str, rect = R_text, scaling = -1, stroke_rgba = mcolor_fg,
                 align = (2,0), font = S.month.font, measure = mmeasure, shadow = mshad)
        cr.restore()

