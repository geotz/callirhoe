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

"""base layout module -- others may inherit from this one"""

import optparse
from lib.xcairo import *
from lib.geom import *
from math import floor, ceil, sqrt

def get_parser(layout_name):
    """get the parser object for the layout command-line arguments

    @param layout_name: corresponding python module (.py file)
    @rtype: optparse.OptionParser
    """
    lname = layout_name.split(".")[1]
    parser = optparse.OptionParser(usage="%prog (...) --layout " + lname + " [options] (...)",add_help_option=False)
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
    parser.add_option("--short-daycell-ratio", type="float", default=2.5,
                      help="ratio threshold for day cells below which short version is drawn [%default]")
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
    parser.add_option("--no-shadow", action="store_true", default=False,
                      help="disable box shadows")
    parser.add_option("--opaque", action="store_true", default=False,
                      help="make background opaque (white fill)")
    parser.add_option("--swap-colors", action="store_true", default=False,
                      help="swap month colors for even/odd years")
    parser.add_option("--fractal", action="store_true", default=False,
                      help="2x2 fractal layout; overrides rows=2, cols=2, z-order=increasing")
    return parser


class DayCell(object):
    """class Holding a day cell to be drawn

    @type day: int
    @ivar day: day of week
    @ivar header: header string
    @ivar footer: footer string
    @ivar theme: (Style class,Geometry class,Language module) tuple
    @type show_day_name: bool
    @ivar show_day_name: whether day name is displayed
    """
    def __init__(self, day, header, footer, theme, show_day_name):
        self.day = day
        self.header = header
        self.footer = footer
        self.theme = theme
        self.show_day_name = show_day_name

    def _draw_short(self, cr, rect):
        """render the day cell in short mode"""
        S,G,L = self.theme
        x, y, w, h = rect
        day_of_month, day_of_week = self.day
        draw_box(cr, rect, S.frame, S.bg, mm_to_dots(S.frame_thickness))
        R = rect_rel_scale(rect, G.size[0], G.size[1])
        if self.show_day_name:
            Rdom, Rdow = rect_hsplit(R, *G.mw_split)
        else:
            Rdom = R
        valign = 0 if self.show_day_name else 2
        # draw day of month (number)
        draw_str(cr, text = str(day_of_month), rect = Rdom, scaling = -1, stroke_rgba = S.fg,
                 align = (2,valign), font = S.font, measure = "88")
        # draw name of day
        if self.show_day_name:
            draw_str(cr, text = L.day_name[day_of_week][0], rect = Rdow, scaling = -1, stroke_rgba = S.fg,
                     align = (2,valign), font = S.font, measure = "88")
        # draw header
        if self.header:
            R = rect_rel_scale(rect, G.header_size[0], G.header_size[1], 0, -1.0 + G.header_align)
            draw_str(cr, text = self.header, rect = R, scaling = -1, stroke_rgba = S.header,
                font = S.header_font) # , measure = "MgMgMgMgMgMg"
        # draw footer
        if self.footer:
            R = rect_rel_scale(rect, G.footer_size[0], G.footer_size[1], 0, 1.0 - G.footer_align)
            draw_str(cr, text = self.footer, rect = R, scaling = -1, stroke_rgba = S.footer,
                font = S.footer_font, measure = "MgMgMg")

    def _draw_long(self, cr, rect):
        """render the day cell in long mode"""
        S,G,L = self.theme
        x, y, w, h = rect
        day_of_month, day_of_week = self.day
        draw_box(cr, rect, S.frame, S.bg, mm_to_dots(S.frame_thickness))
        R1, Rhf = rect_hsplit(rect, *G.hf_hsplit)
        if self.show_day_name:
            R = rect_rel_scale(R1, G.size[2], G.size[3])
            Rdom, Rdow = rect_hsplit(R, *G.mw_split)
        else:
            Rdom = rect_rel_scale(R1, G.size[0], G.size[1])
        valign = 0 if self.show_day_name else 2
        # draw day of month (number)
        draw_str(cr, text = str(day_of_month), rect = Rdom, scaling = -1, stroke_rgba = S.fg,
                 align = (2,valign), font = S.font, measure = "88")
        # draw name of day
        if self.show_day_name:
            draw_str(cr, text = L.day_name[day_of_week], rect = Rdow, scaling = -1, stroke_rgba = S.fg,
                     align = (0,valign), font = S.font, measure = "M")
        Rh, Rf = rect_vsplit(Rhf, *G.hf_vsplit)
        # draw header
        if self.header:
            draw_str(cr, text = self.header, rect = Rh, scaling = -1, stroke_rgba = S.header, align = (1,2),
                 font = S.header_font)
        # draw footer
        if self.footer:
            draw_str(cr, text = self.footer, rect = Rf, scaling = -1, stroke_rgba = S.footer, align = (1,2),
                 font = S.footer_font)

    def draw(self, cr, rect, short_thres):
        """automatically render a short or long day cell depending on threshold I{short_thres}

        If C{rect} ratio is less than C{short_thres} then short mode is chosen, otherwise long mode.
        """
        if rect_ratio(rect) < short_thres:
            self._draw_short(cr, rect)
        else:
            self._draw_long(cr, rect)


class CalendarRenderer(object):
    """base monthly calendar renderer - others inherit from this

    @ivar Outfile: output file
    @ivar Year: year of first month
    @ivar Month: first month
    @ivar MonthSpan: month span
    @ivar Theme: (Style module,Geometry module,Language module) tuple
    @ivar holiday_provider: L{HolidayProvider} object
    @ivar version_string: callirhoe version string
    @ivar options: parser options object
    """
    def __init__(self, Outfile, Year, Month, MonthSpan, Theme, holiday_provider, version_string, options):
        self.Outfile = Outfile
        self.Year = Year
        self.Month = Month
        self.MonthSpan = MonthSpan
        self.Theme = Theme
        self.holiday_provider = holiday_provider
        self.version_string = version_string
        self.options = options

    def _draw_month(self, cr, rect, month, year):
        """this method renders a calendar month, it B{should be overridden} in any subclass

        @param cr: cairo context
        @param rect: rendering rect
        @param month: month
        @param year: year
        """
        raise NotImplementedError("base _draw_month() should be overridden")

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
            print >> sys.stderr, "invalid output format", e.args[0]
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
            Rcal = V0.item_span(39,0)
            Rc = rect_rel_scale(V0.item(39),0.99,0.5,0,0)
        else:
            Rcal = page.Text_rect

        grid = GLayout(Rcal, rows, cols, pad = (mm_to_dots(G.month.padding),)*4)
        mpp = 3 if self.options.fractal else grid.count()  # months per page
        num_pages = int(ceil(self.MonthSpan*1.0/mpp))
        cur_month = self.Month
        cur_year = self.Year
        num_placed = 0
        page_layout = []
        for k in xrange(num_pages):
            page_layout.append([])
            for i in xrange(mpp):
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
            if not self.options.month_with_year and not self.options.no_footer and valid_page:
                year_str = str(yy[0]) if yy[0] == yy[-1] else "%s – %s" % (yy[0],yy[-1])
                draw_str(page.cr, text = year_str, rect = Rc, stroke_rgba = (0,0,0,0.5), scaling = -1,
                         align = (0,0), font = (extract_font_name(S.month.font),0,0))
            if not self.options.no_footer and valid_page:
                draw_str(page.cr, text = "rendered by Callirhoe ver. %s" % self.version_string,
                         rect=Rc, stroke_rgba=(0, 0, 0, 0.5), scaling=-1, align=(1, 0),
                         font=(extract_font_name(S.month.font), 1, 0))
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
