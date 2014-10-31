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
"""  general-purpose geometry routines  """
#                                         #
# *****************************************

def rect_ratio(r):
    """returns the ratio of rect I{r} which is defined as M{width/height}

    @rtype: float
    """
    return r[2]*1.0/r[3]

def rect_rel_scale(r, fw, fh, align_x = 0, align_y = 0):
    """relatively scale a rect

    @type fw: float in [0,1]
    @param fw: width fraction (to be multiplied)
    @type fh: float in [0,1]
    @param fh: height fraction (to be multiplied)
    @type align_x: float in [-1,1]
    @param align_x: determines the relative position of the new rect with respect to
    the old one. A value of 0 aligns in the center, a value of -1 aligns on the
    left, a value of 1 aligns on the right hand side. Intermediate values do
    linear interpolation.
    @type align_y: float in [-1,1]
    @param align_y: Performs vertical (top-bottom) alignment similarly to L{align_x}.
    @rtype: (float,float,float,float)
    """
    x, y, w, h = r
    return (x + (align_x + 1.0)*w*(1 - fw)/2.0,
            y + (align_y + 1.0)*h*(1 - fh)/2.0, w*fw, h*fh)

def rect_pad(r, pad):
    """returns a padded rect by reducing border by the I{pad} tuple (top,left,bottom,right)

    @rtype: (float,float,float,float)
    """
    x, y, w, h = r
    t_, l_, b_, r_ = pad
    return (x + l_, y + t_, w - r_ - l_, h - t_ - b_)

def rect_to_abs(r):
    """get absolute coordinates (x0,y0,x1,y1) from rect definition (x,y,w,h)

    @rtype: (float,float,float,float)
    """
    x, y, w, h = r
    return (x, y, x + w, y + h)

def abs_to_rect(a):
    """get rect definition (x,y,w,h) from absolute coordinates (x0,y0,x1,y1)

    @rtype: (float,float,float,float)
    """
    x1, y1, x2, y2 = a
    return (x1, y1, x2 - x1, y2 - y1)

def rect_from_origin(r):
    """returns a similar rect with top-left corner at (0,0)

    @rtype: (float,float,float,float)
    """
    return (0, 0, r[2], r[3])

def rect_hull(r1,r2):
    """returns the smallest rect containing r1 and r2

    @rtype: (float,float,float,float)
    """
    x1, y1, x2, y2 = rect_to_abs(r1)
    x3, y3, x4, y4 = rect_to_abs(r2)
    return abs_to_rect((min(x1,x3), min(y1,y3), max(x2,x4), max(y2,y4)))

def rect_hsplit(r, f = 0.5, fdist = 0.0):
    """split a rect horizontally

    @type f: float in [0,1]
    @param f: split fraction
    @param fdist: fraction of space to discard before splitting (free space)
    @rtype: ((float,float,float,float),(float,float,float,float))
    @return: tuple (r1,r2) with splits and free space evenly distributed
    before r1, between r1 and r2 and after r2
    """
    x, y, w, h = r
    rw = w*(1.0 - fdist)
    r1 = (x + w*fdist/3.0, y, rw*f, h)
    r2 =(x + rw*f + w*fdist*2.0/3, y, rw*(1 - f), h)
    return (r1, r2)

def rect_vsplit(r, f = 0.5, fdist = 0.0):
    """split a rect vertically, similarly to L{rect_hsplit}

    @rtype: ((float,float,float,float),(float,float,float,float))
    """
    x, y, w, h = r
    rh = h*(1.0 - fdist)
    r1 = (x, y + h*fdist/3.0, w, rh*f)
    r2 = (x, y + rh*f + h*fdist*2.0/3, w, rh*(1 - f))
    return (r1, r2)

def color_mix(a, b, frac):
    """mix two colors

    @type frac: float in [0,1]
    @param frac: amount of first color
    @rtype: tuple
    """
    return map(lambda (x,y): x*frac + y*(1 - frac), zip(a,b))

def color_scale(a, frac):
    """scale color values

    @type frac: float
    @param frac: scale amount (to be multiplied)
    @rtype: tuple
    """
    return map(lambda x: min(1.0,x*frac), a)

def color_auto_fg(bg, light = (1,1,1), dark = (0,0,0)):
    """return I{light} or I{dark} foreground color based on an ad-hoc evaluation of I{bg}

    @rtype: tuple
    """
    return light if (bg[0] + 1.5*bg[1] + bg[2]) < 1.0 else dark

# ********* layout managers ***********

class VLayout(object):
    """vertical layout manager

    @ivar rect: bounding rect for layout -- this rect will be split and the slices assigned to every item
    @ivar nitems: maximum number of items in the layout
    @ivar pad: tuple(top,left,bottom,right) with item padding
    """
    def __init__(self, rect, nitems = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        self.rect = rect
        self.nitems = nitems
        self.pad = pad

    def count(self):
        """return maximum number of items in the layout

        @rtype: int
        """
        return self.nitems

    def resize(self, k):
        """set maximum number of items"""
        self.nitems = k

    def grow(self, delta = 1):
        """increase number of items by I{delta}"""
        self.nitems += delta

    def item(self, i = 0):
        """get rect for item I{i}

        @rtype: (float,float,float,float)
        """
        x, y, w, h = self.rect
        h *= 1.0/self.nitems
        y += i*h
        return rect_pad((x,y,w,h), self.pad)
                
    def item_span(self, n, k = -1):
        """get union of I{k} consecutive items, starting at position I{n}

        @param n: first item
        @param k: number of items, -1 for all remaining items
        @rtype: (float,float,float,float)
        """
        if k < 0: k = (self.count() - n) // 2
        return rect_hull(self.item(k), self.item(k + n - 1))
        
    def items(self):
        """returns a sequence of all items

        @rtype: (float,float,float,float),...
        """
        return map(self.item, range(self.count()))

class HLayout(VLayout):
    """horizontal layout manager defined as a transpose of L{VLayout}"""
    def __init__(self, rect, nitems = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        super(HLayout,self).__init__((rect[1],rect[0],rect[3],rect[2]), 
                                      nitems, (pad[1], pad[0], pad[3], pad[2]))

    def item(self, i = 0):
        """get rect for item I{i}

        @rtype: (float,float,float,float)
        """
        t = super(HLayout,self).item(i)
        return (t[1], t[0], t[3], t[2])
        
class GLayout(object):
    """grid layout manager

    @ivar vrep: internal L{VLayout} for row computations
    @ivar hrep: internal L{HLayout} for column computations
    """
    def __init__(self, rect, nrows = 1, ncols = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        """initialize layout

        @param rect: layout rect (tuple)
        @param nrows: number of rows
        @param ncols: number of columns
        @param pad: cell padding
        """
        self.vrep = VLayout(rect, nrows, (pad[0], 0.0, pad[2], 0.0))
        t = self.vrep.item(0)
        self.hrep = HLayout((rect[0], rect[1], t[2], t[3]), ncols, (0.0, pad[1], 0.0, pad[3]))

    def row_count(self):
        """get (max) number of rows in the grid

        @rtype: int
        """
        return self.vrep.count()

    def col_count(self):
        """get (max) number of columns in the grid

        @rtype: int
        """
        return self.hrep.count()

    def count(self):
        """get total number of cells in the grid (which is M{rows*cols})

        @rtype: int
        """
        return self.row_count()*self.col_count()

    def resize(self, rows, cols):
        """resize grid by specifying new number of rows and columns"""
        self.vrep.resize(rows)
        t = self.vrep.item(0)
        self.hrep = HLayout(t[0:2], t[2:4], cols, (0.0, pad[1], 0.0, pad[3]))

    def item(self, row, col):
        """get rect of cell at position I{row,col}

        @rtype: (float,float,float,float)
        """
        ty = self.vrep.item(row)
        tx = self.hrep.item(col)
        return (tx[0], ty[1], tx[2], tx[3])

    def item_seq(self, k, column_wise = False):
        """get rect of cell at position I{k} column-wise or row-wise

        @rtype: (float,float,float,float)
        """
        if not column_wise:
            row, col = k // self.col_count(), k % self.col_count()
        else:
            col, row = k // self.row_count(), k % self.row_count()
        return self.item(row, col)
        
    def items(self, column_wise = False):
        """get sequence of rects of cells column-wise or row-wise

        @rtype: (float,float,float,float),...
        """
        return map(self.item_seq, range(self.count()))

    def row_items(self, row):
        """get sequence of cell rects of a row

        @rtype: (float,float,float,float),...
        """
        return map(lambda x: self.item(row, x), range(self.col_count()))
        
    def col_items(self, col):
        """get sequence of cell rects of a column

        @rtype: (float,float,float,float),...
        """
        return map(lambda x: self.item(x, col), range(self.row_count()))
        
        
    def item_span(self, nr, nc, row = -1, col = -1):
        """get union of cell rects spanning a subgrid

        @param nr: number of spanning rows
        @param nc: number of spanning columns
        @param row: starting row, -1 for vertically centered
        @param col: starting column, -1 for horizontally centered
        @rtype: (float,float,float,float)
        """
        if row < 0: row = (self.row_count() - nr) // 2
        if col < 0: col = (self.col_count() - nc) // 2
        return rect_hull(self.item(row, col), self.item(row + nr - 1, col + nc - 1))
