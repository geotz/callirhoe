# -*- coding: utf-8 -*-
#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012 George M. Tzoumas

#    Sparse Layout Module
#    Copyright (C) 2013 Neels Hofmeyr

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

"""sparse layout"""

from lib.xcairo import *
from lib.geom import *
import calendar
import optparse
import sys
from datetime import date, timedelta

import _base

# TODO: merge with base parser...
def get_parser(layout_name):
    """get the parser object for the layout command-line arguments

    @param layout_name: corresponding python module (.py file)
    @rtype: optparse.OptionParser
    """
    lname = layout_name.split(".")[1]
    parser = optparse.OptionParser(usage="%prog (...) --layout " + lname + " [options] (...)",add_help_option=False)
    parser.add_option("--rows", type="int", default=1, help="force grid rows [%default]")
    parser.add_option("--cols", type="int", default=3,
                      help="force grid columns [%default]; if ROWS and COLS are both non-zero, "
                      "calendar will span multiple pages as needed; if one value is zero, it "
                      "will be computed automatically in order to fill exactly 1 page")
    parser.add_option("--grid-order", choices=["row","column"],default="row",
                      help="either `row' or `column' to set grid placing order row-wise or column-wise [%default]")
    parser.add_option("--z-order", choices=["auto", "increasing", "decreasing"], default="auto",
                      help="either `increasing' or `decreasing' to set whether next month (in grid order) "
                      "lies above or below the previously drawn month; this affects shadow casting, "
                      "since rendering is always performed in increasing z-order; specifying `auto' "
                      "selects increasing order if and only if sloppy boxes are enabled [%default]")
    parser.add_option("--month-with-year", action="store_true", default=False,
                      help="displays year together with month name, e.g. January 1980; suppresses year from footer line")
    parser.add_option("--no-footer", action="store_true", default=False,
                      help="disable footer line (with year and rendered-by message)")
    parser.add_option("--symmetric", action="store_true", default=False,
                      help="force symmetric mode (equivalent to --geom-var=month.symmetric=1). "
                      "In symmetric mode, day cells are equally sized and all month boxes contain "
                      "the same number of (possibly empty) cells, independently of how many days or "
                      "weeks per month. In asymmetric mode, empty rows are eliminated, by slightly "
                      "resizing day cells, in order to have uniform month boxes.")
    parser.add_option("--padding", type="float", default=None,
                      help="set month box padding (equivalent to --geom-var=month.padding=PADDING)")
    parser.add_option("--no-shadow", action="store_true", default=False,
                      help="disable box shadows")
    parser.add_option("--opaque", action="store_true", default=False,
                      help="make background opaque (white fill)")
    parser.add_option("--swap-colors", action="store_true", default=False,
                      help="swap month colors for even/odd years")
    parser.add_option("--fractal", action="store_true", default=False,
                      help=optparse.SUPPRESS_HELP)
    return parser

parser = get_parser(__name__)

def _draw_day_cell(cr, rect, day, header, footer, theme, show_day_name, text_height=None):
    ds,G,L = theme
    year, month, day_of_month, day_of_week = day
    draw_box(cr, rect, ds.bg, ds.bg, mm_to_dots(ds.frame_thickness))

    if day_of_month > 1:
      x, y, w, h = rect
      draw_line(cr, (x, y, w, 0), ds.frame, mm_to_dots(ds.frame_thickness))

    if (text_height is not None) and (text_height > 0):
      x, y, w, h = rect
      h_diff = h - text_height
      if h_diff > 0:
        y += h_diff / 2
        h = text_height
      rect = (x, y, w, h)

    x, y, w, h = rect
    ww = h
    Rleft = (x + 0.1 * h, y + 0.2 * h, ww - 0.2 * h, .6 * h)
    Rmiddle = (x + h, y, ww, h)
    Rmiddle_top = (x + h + 0.1 * h, y + 0.2 * h, ww, .18 * h)
    bottom_h = .8 * h
    Rmiddle_bottom = (x + h + 0.1 * h, y + h - bottom_h, ww, bottom_h - 0.2 * h)
    #Rmiddle_top = rect_rel_scale(Rmiddle_top, .8, 0.6)
    #Rmiddle_bottom = rect_rel_scale(Rmiddle, .8, 0.6)
    Rright_header = (x + 2*h, y + 0.1 * h, w - 2 * ww - 0.2 * ww, 0.28 * h)
    Rright_footer = (x + 2*h, y + 0.6 * h, w - 2 * ww - 0.2 * ww, 0.28 * h)
    x, y, w, h = Rmiddle_bottom
    hh = h
    h = float(h) * 0.6
    y += float(hh) - h
    Rmiddle_bottom = (x, y, w, h)
    valign = 0 if show_day_name else 2
    # draw day of month (number)
    draw_str(cr, text = str(day_of_month), rect = Rleft, scaling = -1, stroke_rgba = ds.fg,
             align = (1,valign), font = ds.font, measure = "88")
    # draw name of day
    if show_day_name:
        draw_str(cr, text = L.day_name[day_of_week], rect = Rmiddle_bottom,
            scaling = -1, stroke_rgba = ds.fg, align = (0,valign),
            font = ds.font, measure = "Mo")
        # week number
        if day_of_week == 0 or (day_of_month == 1 and month == 1):
          week_nr = date(year, month, day_of_month).isocalendar()[1]
          draw_str(cr, text = "%s%d" % (L.week_of_year_prefix, week_nr), rect = Rmiddle_top,
              scaling = -1, stroke_rgba = ds.fg, align = (0,valign),
              font = ds.header_font, measure = "W88")

    if header:
        draw_str(cr, text = header, rect = Rright_header, scaling = -1,
          stroke_rgba = ds.header, align = (1,1), font = ds.header_font,
          measure='MgMgMgMgMgMgMgMgMg')
    if footer:
        draw_str(cr, text = footer, rect = Rright_footer, scaling = -1,
            stroke_rgba = ds.footer, align = (1,1), font = ds.header_font,
            measure='MgMgMgMgMgMgMgMgMg')

class CalendarRenderer(_base.CalendarRenderer):
    """sparse layout class"""
    def _draw_month(self, cr, rect, month, year):
        S,G,L = self.Theme
        make_sloppy_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

        day, span = calendar.monthrange(year, month)
        wmeasure = 'A'*max(map(len,L.day_name))
        mmeasure = 'A'*max(map(len,L.month_name))

        rows = 31 if G.month.symmetric else span
        grid = VLayout(rect_from_origin(rect), 32) # title bar always symmetric
        dom_grid = VLayout(grid.item_span(31,1), rows)

        # determine text height
        tmp_grid = VLayout(grid.item_span(31,1), 31)
        text_height = tmp_grid.item(0)[3]

        # draw box shadow
        if S.month.box_shadow:
            f = S.month.box_shadow_size
            shad = (f,-f) if G.landscape else (f,f)
            draw_shadow(cr, rect_from_origin(rect), shad)

        # draw day cells
        for dom in range(1,span+1):
            R = dom_grid.item(dom-1)
            holiday_tuple = self.holiday_provider(year, month, dom, day)
            day_style = holiday_tuple[2]
            header = holiday_tuple[0]
            footer = holiday_tuple[1]
            _draw_day_cell(cr, rect = R, day = (year, month, dom, day),
                          header = header, footer = footer,
                          theme = (day_style, G.dom, L), show_day_name = True,
                          text_height = text_height)

            day = (day + 1) % 7

        # draw month title (name)
        mcolor = S.month.color_map_bg[year%2][month]
        mcolor_fg = S.month.color_map_fg[year%2][month]
        R_mb = grid.item(0)
        R_text = rect_rel_scale(R_mb, 1, 0.5)
        mshad = None
        if S.month.text_shadow:
            f = S.month.text_shadow_size
            mshad = (f,-f) if G.landscape else (f,f)
        draw_str(cr, text = L.month_name[month], rect = R_text, scaling = -1, stroke_rgba = mcolor_fg,
                 align = (2,0), font = S.month.font, measure = mmeasure, shadow = mshad)
        cr.restore()
