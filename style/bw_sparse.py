#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012 George M. Tzoumas

#    Sparse Style Definition
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

# --- style.bw_sparse ---

"""module defining the black & white sparse style

to be used with sparse layout
"""

class dow:
    """day of week style"""
    fg = (0,0,0)
    frame_thickness = 0.1
    frame = (.5, .5, .5)
    font = "Arial"
    
class dom:
    """day of month style"""
    bg = (1,1,1)
    frame = (.9, .9, .9)
    frame_thickness = 0.1
    fg = (0.3,0.3,0.3)
    font = "Times New Roman"
    header = (0.3,0.3,0.3)
    footer = header
    header_font = footer_font = "Arial"

class dom_holiday(dom):
    """day of month (holiday, indicated by the OFF flag in the holiday file)"""
    bg = (0.80,0.80,0.80)

class dom_weekend(dom_holiday):
    """day of month style (weekend)"""
    font = ("Times New Roman", 0, 1)

class dom_weekend_holiday(dom_weekend):
    """day of month (weekend & holiday)"""
    pass

class dom_multi(dom_holiday):
    """day of month (multi-day holiday)"""
    pass

class dom_weekend_multi(dom_weekend_holiday):
    """day of month (weekend in multi-day holiday)"""
    pass

class month:    
    """month style"""
    font = ("Times New Roman", 0, 1)
    frame = (0,0,0)
    frame_thickness = 0.2
    bg = (1,1,1)
    color_map = ((1,1,1),)*13
    color_map_bg = (((1,1,1),)*13,((.8,.8,.8),)*13)
    color_map_fg = (((0,0,0),)*13,((0,0,0),)*13)
    box_shadow = False
    text_shadow = False
