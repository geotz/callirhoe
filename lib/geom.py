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
#    general-purpose geometry routines    #
#                                         #
# *****************************************

def rect_ratio(r):
    return r[2]*1.0/r[3]

def rect_rel_scale(r, fw, fh, align_x = 0, align_y = 0):
    x, y, w, h = r
    return (x + (align_x + 1.0)*w*(1 - fw)/2.0,
            y + (align_y + 1.0)*h*(1 - fh)/2.0, w*fw, h*fh)

def rect_pad(r, pad):
    x, y, w, h = r
    t_, l_, b_, r_ = pad
    return (x + l_, y + t_, w - r_ - l_, h - t_ - b_)

def rect_to_abs(r):
    x, y, w, h = r
    return (x, y, x + w, y + h)

def abs_to_rect(a):
    x1, y1, x2, y2 = a
    return (x1, y1, x2 - x1, y2 - y1)

def rect_from_origin(r):
    return (0, 0, r[2], r[3])

def rect_hull(r1,r2):
    x1, y1, x2, y2 = rect_to_abs(r1)
    x3, y3, x4, y4 = rect_to_abs(r2)
    return abs_to_rect((min(x1,x3), min(y1,y3), max(x2,x4), max(y2,y4)))

def rect_hsplit(r, f = 0.5, fdist = 0.0):
    x, y, w, h = r
    rw = w*(1.0 - fdist)
    r1 = (x + w*fdist/3.0, y, rw*f, h)
    r2 =(x + rw*f + w*fdist*2.0/3, y, rw*(1 - f), h)
    return (r1, r2)

def rect_vsplit(r, f = 0.5, fdist = 0.0):
    x, y, w, h = r
    rh = h*(1.0 - fdist)
    r1 = (x, y + h*fdist/3.0, w, rh*f)
    r2 = (x, y + rh*f + h*fdist*2.0/3, w, rh*(1 - f))
    return (r1, r2)

def color_mix(a, b, frac):
    return map(lambda (x,y): x*frac + y*(1 - frac), zip(a,b))

def color_scale(a, frac):
    return map(lambda x: min(1.0,x*frac), a)

def color_auto_fg(bg, light = (1,1,1), dark = (0,0,0)):
    return light if (bg[0] + 1.5*bg[1] + bg[2]) < 1.0 else dark

# ********* layout managers ***********

class VLayout(object):
    def __init__(self, rect, nitems = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        self.rect = rect
        self.nitems = nitems
        self.pad = pad

    def count(self):
        return self.nitems

    def resize(self, k):
        self.nitems = k

    def grow(self, delta = 1):
        self.nitems += delta

    def item(self, i = 0):
        x, y, w, h = self.rect
        h *= 1.0/self.nitems
        y += i*h
        return rect_pad((x,y,w,h), self.pad)
                
    def item_span(self, n, k = -1):
        if k < 0: k = (self.count() - n) // 2
        return rect_hull(self.item(k), self.item(k + n - 1))
        
    def items(self):
        return map(self.item, range(self.count()))

class HLayout(VLayout): # transpose of VLayout
    def __init__(self, rect, nitems = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        super(HLayout,self).__init__((rect[1],rect[0],rect[3],rect[2]), 
                                      nitems, (pad[1], pad[0], pad[3], pad[2]))

    def item(self, i = 0):
        t = super(HLayout,self).item(i)
        return (t[1], t[0], t[3], t[2])
        
class GLayout:
    def __init__(self, rect, nrows = 1, ncols = 1, pad = (0.0,0.0,0.0,0.0)): # TLBR
        self.vrep = VLayout(rect, nrows, (pad[0], 0.0, pad[2], 0.0))
        t = self.vrep.item(0)
        self.hrep = HLayout((rect[0], rect[1], t[2], t[3]), ncols, (0.0, pad[1], 0.0, pad[3]))

    def row_count(self):
        return self.vrep.count()

    def col_count(self):
        return self.hrep.count()

    def count(self):
        return self.row_count()*self.col_count()

    def resize(self, rows, cols):
        self.vrep.resize(rows)
        t = self.vrep.item(0)
        self.hrep = HLayout(t[0:2], t[2:4], cols, (0.0, pad[1], 0.0, pad[3]))

    def item(self, row, col):
        ty = self.vrep.item(row)
        tx = self.hrep.item(col)
        return (tx[0], ty[1], tx[2], tx[3])

    def item_seq(self, k, column_wise = False):
        if not column_wise:
            row, col = k // self.col_count(), k % self.col_count()
        else:
            col, row = k // self.row_count(), k % self.row_count()
        return self.item(row, col)
        
    def items(self, column_wise = False):
        return map(self.item_seq, range(self.count()))

    def row_items(self, row):
        return map(lambda x: self.item(row, x), range(self.col_count()))
        
    def col_items(self, col):
        return map(lambda x: self.item(x, col), range(self.row_count()))
        
        
    def item_span(self, nr, nc, row = -1, col = -1):
        if row < 0: row = (self.row_count() - nr) // 2
        if col < 0: col = (self.col_count() - nc) // 2
        return rect_hull(self.item(row, col), self.item(row + nr - 1, col + nc - 1))
