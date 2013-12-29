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

# --- layouts.classic ---

from lib.xcairo import *
from lib.geom import *
from math import floor, ceil, sqrt
import calendar
import optparse
import sys
from datetime import date, timedelta

parser = optparse.OptionParser(usage="%prog (...) --layout classic [options] (...)",add_help_option=False)
parser.add_option("--rows", type="int", default=0, help="force grid rows [%default]")
parser.add_option("--cols", type="int", default=0, 
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
parser.add_option("--long-daycells", action="store_const", const=0.0, dest="short_daycell_ratio",
                  help="force use of only long daycells")
parser.add_option("--short-daycells", action="store_const", const=1.0e6, dest="short_daycell_ratio",
                  help="force use of only short daycells")
parser.add_option("--bar", action="store_const", const=1.0e6, dest="month_bar_ratio",
                  help="force month drawing in bar mode")
parser.add_option("--matrix", action="store_const", const=0, dest="month_bar_ratio",
                  help="force month drawing in matrix mode")
parser.add_option("--short-daycell-ratio", type="float", default=2.5,
                  help="ratio threshold for day cells below which short version is drawn [%default]")
parser.add_option("--month-bar-ratio", type="float", default=0.7,
                  help="ratio threshold for month box, below which bar is drawn [%default]")
parser.add_option("--no-footer", action="store_true", default=False,
                  help="disable footer line (with year and rendered-by message)")
parser.add_option("--symmetric", action="store_true", default=False,
                  help="force symmetric mode (equivalent to --geom-var=month.symmetric=1). "
                  "In symmetric mode, day cells are equally sized and all month boxes contain "
                  "the same number of (possibly empty) cells, independently of how many days or "
                  "weeks per month. In asymmetric mode, empty rows are eliminated, by slightly "
                  "resizing day cells, in order to have uniform month boxes.")
parser.add_option("--padding", type="float", default=None,
                  help="set month box padding (equivalent to --geom-var=month.padding=PADDING); "
                  "month bars look better with smaller padding, while matrix mode looks better with "
                  "larger padding")
parser.add_option("--no-shadow", action="store_true", default=None,
                  help="disable box shadows")
parser.add_option("--opaque", action="store_true", default=False,
                  help="make background opaque (white fill)")
parser.add_option("--swap-colors", action="store_true", default=None,
                  help="swap month colors for even/odd years")


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
    draw_box(cr, rect, S.frame, S.bg, mm_to_dots(S.frame_thickness))
    R = rect_rel_scale(rect, G.size[0], G.size[1])
    if show_day_name:
        Rdom, Rdow = rect_hsplit(R, *G.mw_split)
    else:
        Rdom = R
    valign = 0 if show_day_name else 2
    # draw day of month (number)
    draw_str(cr, text = str(day_of_month), rect = Rdom, stretch = -1, stroke_rgba = S.fg,
             align = (2,valign), font = S.font, measure = "88")
    # draw name of day
    if show_day_name:
        draw_str(cr, text = calendar.day_name[day_of_week][0], rect = Rdow, stretch = -1, stroke_rgba = S.fg,
                 align = (2,valign), font = S.font, measure = "88")
    # draw header
    if header:
        R = rect_rel_scale(rect, G.header_size[0], G.header_size[1], 0, -1.0 + G.header_align)
        draw_str(cr, text = header, rect = R, stretch = -1, stroke_rgba = S.header, font = S.header_font)
    # draw footer
    if footer:
        R = rect_rel_scale(rect, G.footer_size[0], G.footer_size[1], 0, 1.0 - G.footer_align)
        draw_str(cr, text = footer, rect = R, stretch = -1, stroke_rgba = S.footer, font = S.footer_font)

def _draw_day_cell_long(cr, rect, day, header, footer, theme, show_day_name):
    S,G = theme
    x, y, w, h = rect
    day_of_month, day_of_week = day
    draw_box(cr, rect, S.frame, S.bg, mm_to_dots(S.frame_thickness))
    R1, Rhf = rect_hsplit(rect, *G.hf_hsplit)
    if show_day_name:
        R = rect_rel_scale(R1, G.size[2], G.size[3])
        Rdom, Rdow = rect_hsplit(R, *G.mw_split)
    else:
        Rdom = rect_rel_scale(R1, G.size[0], G.size[1])
    valign = 0 if show_day_name else 2
    # draw day of month (number)
    draw_str(cr, text = str(day_of_month), rect = Rdom, stretch = -1, stroke_rgba = S.fg,
             align = (2,valign), font = S.font, measure = "88")
    # draw name of day
    if show_day_name:
        draw_str(cr, text = calendar.day_name[day_of_week][0], rect = Rdow, stretch = -1, stroke_rgba = S.fg,
                 align = (2,valign), font = S.font, measure = "M")
    Rh, Rf = rect_vsplit(Rhf, *G.hf_vsplit)
    # draw header
    if header:
        draw_str(cr, text = header, rect = Rh, stretch = -1, stroke_rgba = S.header, align = (1,2),
             font = S.header_font)
    # draw footer
    if footer:
        draw_str(cr, text = footer, rect = Rf, stretch = -1, stroke_rgba = S.footer, align = (1,2),
             font = S.footer_font)

def draw_day_cell(cr, rect, day, header, footer, theme, show_day_name, short_thres):
    if rect_ratio(rect) < short_thres:
        _draw_day_cell_short(cr, rect, day, header, footer, theme, show_day_name)
    else:
        _draw_day_cell_long(cr, rect, day, header, footer, theme, show_day_name)

def draw_month_matrix(cr, rect, month, year, theme, holiday_provider, daycell_thres):
    S,G = theme
    apply_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

    day, span = calendar.monthrange(year, month)
    weekrows = 6 if G.month.symmetric else weekrows_of_month(year, month)
    dom = -day + 1;
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
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
        draw_str(cr, text = calendar.day_name[col], rect = R_text, stretch = -1, stroke_rgba = S.dow.fg,
                 align = (2,0), font = S.dow.font, measure = wmeasure)
        
    # draw day cells
    for row in range(weekrows):
        for col in range(7):
            R = dom_grid.item(row, col)
            if dom > 0 and dom <= span:
                holiday_tuple = holiday_provider(year, month, dom, col)
                day_style = holiday_tuple[2]
                draw_day_cell(cr, rect = R, day = (dom, col),
                              header = holiday_tuple[0], footer = holiday_tuple[1], theme = (day_style, G.dom), show_day_name = False,
                              short_thres = daycell_thres)
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
    title_str = calendar.month_name[month]
    if options.month_with_year: title_str += ' ' + str(year)
    draw_str(cr, text = title_str, rect = R_text, stretch = -1, stroke_rgba = mcolor_fg,
             align = (2,0), font = S.month.font, measure = mmeasure, shadow = mshad)
    cr.restore()

def draw_month_bar(cr, rect, month, year, theme, holiday_provider, daycell_thres):
    S,G = theme
    apply_rect(cr, rect, G.month.sloppy_dx, G.month.sloppy_dy, G.month.sloppy_rot)

    day, span = calendar.monthrange(year, month)
    wmeasure = 'A'*max(map(len,calendar.day_name))
    mmeasure = 'A'*max(map(len,calendar.month_name))
    
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
            holiday_tuple = holiday_provider(year, month, dom, day)
            day_style = holiday_tuple[2]
            draw_day_cell(cr, rect = R, day = (dom, day), header = holiday_tuple[0], footer = holiday_tuple[1],
                          theme = (day_style, G.dom), show_day_name = True, short_thres = daycell_thres)
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
    draw_str(cr, text = calendar.month_name[month], rect = R_text, stretch = -1, stroke_rgba = mcolor_fg,
             align = (2,0), font = S.month.font, measure = mmeasure, shadow = mshad)
    cr.restore()

def draw_month(cr, rect, month, year, theme, holiday_provider, bar_thres = 0.7, daycell_thres = 2.5):
    if rect_ratio(rect) >= bar_thres:
        draw_month_matrix(cr, rect, month, year, theme, holiday_provider, daycell_thres)
    else:
        draw_month_bar(cr, rect, month, year, theme, holiday_provider, daycell_thres)

#1   1   1
#2   2   1
#3   3   1

#4   2   2
#5   3   2
#6   3   2
#7   4   2
#8   4   2

#9   3   3
#10  4   3
#11  4   3
#12  4   3

#rows = 0
#cols = 0

def draw_calendar(Outfile, Year, Month, MonthSpan, Theme, holiday_provider, version_string):
    S,G = Theme
    rows, cols = options.rows, options.cols

    if options.symmetric:
        G.month.symmetric = True
    if options.padding is not None:
        G.month.padding = options.padding
    if options.no_shadow == True:
        S.month.box_shadow = False
    if options.swap_colors:
        S.month.color_map_bg = (S.month.color_map_bg[1], S.month.color_map_bg[0]) 
        S.month.color_map_fg = (S.month.color_map_fg[1], S.month.color_map_fg[0]) 
        
    try:
        page = PageWriter(Outfile, G.landscape, G.pagespec, G.border, not options.opaque)
    except InvalidFormat as e:
        print >> sys.stderr, "invalid output format", e.args[0]
        sys.exit(1)
    
    if rows == 0 and cols == 0:
#        if MonthSpan < 4: 
#            cols = 1; rows = MonthSpan
#        elif MonthSpan < 9: 
#            cols = 2; rows = int(math.ceil(MonthSpan/2.0))
#        else:
            # TODO: improve this heuristic
            cols = int(floor(sqrt(MonthSpan)))
            rows = cols
            if rows*cols < MonthSpan: rows += 1
            if rows*cols < MonthSpan: rows += 1
            if rows*cols < MonthSpan: cols += 1; rows -= 1
            if G.landscape: rows, cols = cols, rows
    elif rows == 0:
        rows = int(ceil(MonthSpan*1.0/cols))
    elif cols == 0:
        cols = int(ceil(MonthSpan*1.0/rows))
    G.landscape = page.landscape  # PNG is pseudo-landscape (portrait with width>height)
    
    if not options.no_footer:
        V0 = VLayout(page.Text_rect, 40, (1,)*4)
        Rcal = V0.item_span(39,0)
        Rc = rect_rel_scale(V0.item(39),1,0.5,0,0)
    else:
        Rcal = page.Text_rect

    grid = GLayout(Rcal, rows, cols, pad = (mm_to_dots(G.month.padding),)*4)
    mpp = grid.count() # months per page
    num_pages = int(ceil(MonthSpan*1.0/mpp))
    cur_month = Month
    cur_year = Year
    num_placed = 0
    page_layout = []
    for k in xrange(num_pages):
        page_layout.append([])
        for i in xrange(mpp):
            page_layout[k].append((cur_month,cur_year))
            num_placed += 1
            cur_month += 1
            if cur_month > 12: cur_month = 1; cur_year += 1
            if num_placed >= MonthSpan: break
            
    num_pages_written = 0
    
    z_order = options.z_order
    if z_order == "auto":
        if G.month.sloppy_dx != 0 or G.month.sloppy_dy != 0 or G.month.sloppy_rot != 0:
            z_order = "decreasing"
        else:
            z_order = "increasing"
    for p in page_layout:
        num_placed = 0
        yy = [p[0][1]]
        if z_order == "decreasing": p.reverse()
        for (m,y) in p:
            k = len(p) - num_placed - 1 if z_order == "decreasing" else num_placed 
            draw_month(page.cr, grid.item_seq(k, options.grid_order == "column"), 
                       month=m, year=y, theme = Theme, holiday_provider = holiday_provider,
                       bar_thres = options.month_bar_ratio, daycell_thres = options.short_daycell_ratio)
            num_placed += 1
            if (y > yy[-1]): yy.append(y)
        if not options.month_with_year and not options.no_footer:
            year_str = str(yy[0]) if yy[0] == yy[-1] else "%s – %s" % (yy[0],yy[-1])
            draw_str(page.cr, text = year_str, rect = Rc, stroke_rgba = (0,0,0,0.5), stretch = -1, 
                     align = (0,0), font = (extract_font_name(S.month.font),0,0))
        if not options.no_footer:
            draw_str(page.cr, text = "rendered by Callirhoe ver. %s" % version_string,
                     rect = Rc, stroke_rgba = (0,0,0,0.5), stretch = -1, align = (1,0),
                     font = (extract_font_name(S.month.font),1,0))
        num_pages_written += 1
        page.end_page()
        if num_pages_written < num_pages:
            page.new_page()
