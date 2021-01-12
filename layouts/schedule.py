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

"""schedule layout"""

from lib.xcairo import *
from lib.geom import *
import calendar
import sys
from datetime import date, timedelta
from math import floor, ceil, sqrt

from . import _base

parser = _base.get_parser(__name__)
parser.add_option("--phantom-days", action="store_true", default=False,
                  help="show days from previous/next month in the unused cells")
parser.add_option("--lightweight", action="store_true", default=False,
                  help="lightweight cell rendering (lighter/no borders)")
parser.add_option("--lw-inner-padding", type="float", default=1.5,
                  help="inner padding for month box in lightweight mode")

SCHEDULE_NAMES = ["Alice", "Bob", "Eve"]
SCHEDULE_COLORS = [(0.4,0.4,0.85,1), (0.4,0.85,0.4,1), (0.85,0.4,0.4,1)]
SCHEDULE_START = date(2020, 12, 28)


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
        wmeasure = 'A'*max(list(map(len,L.day_name)))
        mmeasure = 'A'*max(list(map(len,L.month_name)))
        if self.options.month_with_year:
            mmeasure += 'A'*(len(str(year))+1)

        if self.options.lightweight:
            pad = mm_to_dots(self.options.lw_inner_padding); # compute padding from mm to our coordinate system
            rect2 = rect_pad(rect, (pad,)*4) # shrink month rect by pad
            offset = (rect2[0]-rect[0],rect2[1]-rect[1]) # get offset of new top-left corner wrt prev rect
            rect2 = rect_from_origin(rect2); # move new rect to origin (for grid computation)
            rect2 = (rect2[0]+offset[0],rect2[1]+offset[1],rect2[2],rect2[3]) # compensate for offset so that it is correctly centered
        else:
            rect2 = rect_from_origin(rect)
        grid = GLayout(rect2, 7, 7)
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
            draw_box(cr, rect = R, stroke_rgba = None if self.options.lightweight else S.dom.frame,
                     fill_rgba = S.dom.bg if col < 5 else S.dom_weekend.bg,
                     stroke_width = mm_to_dots(S.dow.frame_thickness), 
                     lightweight = self.options.lightweight)
            R_text = rect_rel_scale(R, 1, 0.5)
            draw_str(cr, text = L.day_name[col], rect = R_text, scaling = -1, stroke_rgba = S.dow.fg,
                     align = (2,0), font = S.dow.font, measure = wmeasure)
            
        # draw day cells
        iso_y, iso_w, iso_d = date(year,month,1).isocalendar()
        for row in range(weekrows):
            for col in range(7):
                R = dom_grid.item(row, col)
                is_normal = dom > 0 and dom <= span
                if is_normal or self.options.phantom_days:
                    real_year, real_month, real_dom = year, month, dom
                    real_iso_w = iso_w

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
                    idx = ((date(real_year, real_month, real_dom) - SCHEDULE_START).days // 7) % len(SCHEDULE_COLORS)
                    day_style = S.dom(bg=SCHEDULE_COLORS[idx], fg=color_auto_fg(SCHEDULE_COLORS[idx]))
                    dcell = _base.DayCell(day = (real_dom, col, iso_w), header = holiday_tuple[0], footer = holiday_tuple[1],
                                          theme = (day_style, G.dom, L), show_day_name = False, 
                                          lightweight = self.options.lightweight )
                    dcell.draw(cr, R, self.options.short_daycell_ratio)
                else:
                    day_style = S.dom_weekend if col >= 5 else S.dom
                    draw_box(cr, rect = R, stroke_rgba = day_style.frame, fill_rgba = day_style.bg,
                             stroke_width = mm_to_dots(day_style.frame_thickness),
                             lightweight = self.options.lightweight)
                dom += 1
        iso_w += 1
                
        # draw month title (name)
        mcolor = S.month.color_map_bg[year%2][month]
        mcolor_fg = S.month.color_map_fg[year%2][month]
        draw_box(cr, rect = R_mb, stroke_rgba = None if self.options.lightweight else S.month.frame, 
                 fill_rgba = mcolor,
                 stroke_width = mm_to_dots(S.month.frame_thickness),
                 lightweight = self.options.lightweight) # title box
        draw_box(cr, rect = rect_from_origin(rect), stroke_rgba = S.month.frame, fill_rgba = (),
                 stroke_width = mm_to_dots(S.month.frame_thickness),
                 lightweight = self.options.lightweight) # full box
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

    def render(self):
        """main calendar rendering routine"""
        S,G,L = self.Theme
        if self.options.fractal:
            rows = cols = 2
        else:
            rows, cols = self.options.rows, self.options.cols


        if self.options.symmetric:
            G.month.symmetric = True
        if self.options.padding is not None:
            G.month.padding = self.options.padding
        if self.options.no_shadow == True:
            S.month.box_shadow = False
        if self.Year % 2: self.options.swap_colors = not self.options.swap_colors
        if self.options.swap_colors:
            S.month.color_map_bg = (S.month.color_map_bg[1], S.month.color_map_bg[0])
            S.month.color_map_fg = (S.month.color_map_fg[1], S.month.color_map_fg[0])

        try:
            page = PageWriter(self.Outfile, G.pagespec, not self.options.opaque, G.landscape, G.border)
        except InvalidFormat as e:
            print("invalid output format", e.args[0], file=sys.stderr)
            sys.exit(1)

        if rows == 0 and cols == 0:
    #        if MonthSpan < 4:
    #            cols = 1; rows = MonthSpan
    #        elif MonthSpan < 9:
    #            cols = 2; rows = int(math.ceil(MonthSpan/2.0))
    #        else:
                # TODO: improve this heuristic
                cols = int(floor(sqrt(self.MonthSpan)))
                rows = cols
                if rows*cols < self.MonthSpan: rows += 1
                if rows*cols < self.MonthSpan: rows += 1
                if rows*cols < self.MonthSpan: cols += 1; rows -= 1
                if G.landscape: rows, cols = cols, rows
        elif rows == 0:
            rows = int(ceil(self.MonthSpan*1.0/cols))
        elif cols == 0:
            cols = int(ceil(self.MonthSpan*1.0/rows))
        G.landscape = page.landscape  # PNG is pseudo-landscape (portrait with width>height)

        if not self.options.no_footer:
            V0 = VLayout(page.Text_rect, 40, (1,)*4)
            Rcal = V0.item_span(5,33)
            Rh1 = V0.item_span(0,2)
            Rh2 = V0.item_span(3,0)
            Rc = V0.item_span(39,0)
        else:
            Rcal = page.Text_rect

        grid = GLayout(Rcal, rows, cols, pad = (mm_to_dots(G.month.padding),)*4)
        mpp = 3 if self.options.fractal else grid.count()  # months per page
        num_pages = int(ceil(self.MonthSpan*1.0/mpp))
        cur_month = self.Month
        cur_year = self.Year
        num_placed = 0
        page_layout = []
        for k in range(num_pages):
            page_layout.append([])
            for i in range(mpp):
                page_layout[k].append((cur_month,cur_year))
                num_placed += 1
                cur_month += 1
                if cur_month > 12: cur_month = 1; cur_year += 1
                if num_placed >= self.MonthSpan: break

        num_pages_written = 0

        z_order = "increasing" if self.options.fractal else self.options.z_order
        if z_order == "auto":
            if G.month.sloppy_dx != 0 or G.month.sloppy_dy != 0 or G.month.sloppy_rot != 0:
                z_order = "decreasing"
            else:
                z_order = "increasing"
        total_placed = 0
        for p in page_layout:  # [[(month,year),...],...]
            num_placed = 0
            yy = [p[0][1]]
            if z_order == "decreasing": p.reverse()
            for (m,y) in p:
                k = len(p) - num_placed - 1 if z_order == "decreasing" else num_placed
                self._draw_month(page.cr, grid.item_seq(k, self.options.grid_order == "column"),
                           month=m, year=y)
                num_placed += 1
                total_placed += 1
                if y > yy[-1]:
                    yy.append(y)
            # TODO: use full year range in fractal mode
            valid_page = not self.options.fractal or num_pages_written == 0            
            if not self.options.no_footer and valid_page:
                # Draw header
                draw_str(page.cr, text = "{} {} - {} {}".format(L.month_name[p[0][0]], yy[0], L.month_name[p[-1][0]], yy[-1]),
                         rect=Rh1, stroke_rgba=(0, 0, 0, 0.95), scaling=-1, align=(2, 0),
                         font=(extract_font_name(S.month.font), 0, 0))
                draw_str(page.cr, text = "Cleaning schedule",
                         rect=Rh2, stroke_rgba=(0, 0, 0, 0.95), scaling=-1, align=(2, 0),
                         font=(extract_font_name(S.month.font), 0, 0))
                # Draw footer with legend
                Hf = HLayout(Rc, len(SCHEDULE_NAMES), (0,)*4)
                for i in range(Hf.count()):
                    r = rect_rel_scale(Hf.item(i),0.5,0.7,0,0)
                    r_text = rect_rel_scale(r, 1, 0.5, 0, 0)
                    draw_box(page.cr, r, None, SCHEDULE_COLORS[i])
                    draw_str(page.cr, text = SCHEDULE_NAMES[i],
                         rect=r_text, stroke_rgba=color_auto_fg(SCHEDULE_COLORS[i]), scaling=2, align=(2, 2),
                         font=(extract_font_name(S.month.font), 0, 0))
            num_pages_written += 1
            if self.options.fractal:
                if total_placed < self.MonthSpan-1:
                    # undo padding to apply same padding recursively
                    tmp = rect_pad(grid.item_seq(3), (-mm_to_dots(G.month.padding)/2.0,)*4)
                    grid = GLayout(tmp, rows, cols, pad=(mm_to_dots(G.month.padding)/2.0,)*4)
                else:
                    grid = GLayout(grid.item_seq(3), 1, 1)
                if num_pages_written == num_pages:
                    page.end_page()
            else:
                page.end_page()
                if num_pages_written < num_pages:
                    page.new_page()

