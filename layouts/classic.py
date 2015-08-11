# -*- coding: utf-8 -*-
#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012-2015 George M. Tzoumas

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

"""classic layout"""

from lib.xcairo import *
from lib.geom import *
import calendar
import sys
from datetime import date, timedelta

import _base

parser = _base.get_parser(__name__)
parser.add_option("--phantom-days", action="store_true", default=False,
                  help="show days from previous/next month in the unused cells")

def _weekrows_of_month(year, month):
    """returns the number of Monday-Sunday ranges (or subsets of) that a month contains, which are 4, 5 or 6

    @rtype: int
    """
    day,span = calendar.monthrange(year, month)
    if day == 0 and span == 28: return 4
    if day == 5 and span == 31: return 6
    if day == 6 and span >= 30: return 6
    return 5

class CalendarRenderer(_base.CalendarRenderer):
    """classic tiles layout class"""
    def _draw_month(self, cr, rect, month, year):
        S,G,L = self.Theme
        make_sloppy_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

        day, span = calendar.monthrange(year, month)
        weekrows = 6 if G.month.symmetric else _weekrows_of_month(year, month)
        dom = -day + 1;
        wmeasure = 'A'*max(map(len,L.day_name))
        mmeasure = 'A'*max(map(len,L.month_name))
        if self.options.month_with_year:
            mmeasure += 'A'*(len(str(year))+1)

        grid = GLayout(rect_from_origin(rect), 7, 7)
        # 61.8% - 38.2% split (golden)
        R_mb, R_db = rect_vsplit(grid.item_span(1, 7, 0, 0), 0.618)  # month name bar, day name bar
        R_dnc = HLayout(R_db, 7) # day name cells = 1/7-th of day name bar
        dom_grid = GLayout(grid.item_span(6, 7, 1, 0), weekrows, 7)
        
        # draw box shadow
        if S.month.box_shadow:
            f = S.month.box_shadow_size
            shad = (f,-f) if G.landscape else (f,f)
            draw_shadow(cr, rect_from_origin(rect), shad)
            
        # draw day names
        for col in range(7):
            R = R_dnc.item(col)
            draw_box(cr, rect = R, stroke_rgba = S.dom.frame,
                     fill_rgba = S.dom.bg if col < 5 else S.dom_weekend.bg,
                     stroke_width = mm_to_dots(S.dow.frame_thickness))
            R_text = rect_rel_scale(R, 1, 0.5)
            draw_str(cr, text = L.day_name[col], rect = R_text, scaling = -1, stroke_rgba = S.dow.fg,
                     align = (2,0), font = S.dow.font, measure = wmeasure)
            
        # draw day cells
        for row in range(weekrows):
            for col in range(7):
                R = dom_grid.item(row, col)
                is_normal = dom > 0 and dom <= span
                if is_normal or self.options.phantom_days:
                    real_year, real_month, real_dom = year, month, dom

                    # handle phantom days
                    if dom < 1:
                        real_month -= 1
                        if real_month < 1:
                            real_month = 12
                            real_year -= 1
                        real_dom += calendar.monthrange(real_year, real_month)[1]
                    elif dom > span:
                        real_month += 1
                        if real_month > 12:
                            real_month = 1
                            real_year += 1
                        real_dom -= span

                    holiday_tuple = self.holiday_provider(real_year, real_month, real_dom, col)
                    if is_normal:
                        day_style = holiday_tuple[2]
                    else:
                        day_style = S.dom_weekend_phantom if col >= 5 else S.dom_phantom
                    dcell = _base.DayCell(day = (real_dom, col), header = holiday_tuple[0], footer = holiday_tuple[1],
                                          theme = (day_style, G.dom, L), show_day_name = False)
                    dcell.draw(cr, R, self.options.short_daycell_ratio)
                else:
                    day_style = S.dom_weekend if col >= 5 else S.dom
                    draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                             stroke_width = mm_to_dots(day_style.frame_thickness))
                dom += 1
                
        # draw month title (name)
        mcolor = S.month.color_map_bg[year%2][month]
        mcolor_fg = S.month.color_map_fg[year%2][month]
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

