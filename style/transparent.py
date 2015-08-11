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

# --- style.transparent ---

"""module defining the transparent style"""

_fg = (0.5,0,0.5)
_OPACITY = 0.1

class dow:
    """day of week style"""
    fg = (0,0,0)
    frame_thickness = 0.3
    frame = (0.5,0.5,0.5)
    font = "Arial"
    
class dom:
    """day of month style"""
    bg = (1,1,1,_OPACITY)
    frame = (0.5,0.5,0.5)
    frame_thickness = 0.3
    fg = (0,0,0)
    font = "Times New Roman"
    header = (0.3,0.3,0.3)
    footer = header
    header_font = footer_font = "Arial"

class dom_weekend(dom):
    """day of month style (weekend)"""
    bg = (0.8,0.8,0.8,_OPACITY)
    fg = _fg
    font = ("Times New Roman", 0, 1)

class dom_phantom(dom):
    fg = dom.fg + (0.15,)
    header = dom.header + (0.15,)
    footer = dom.footer + (0.15,)

class dom_weekend_phantom(dom_weekend):
    fg = dom_weekend.fg + (0.15,)
    header = dom_weekend.header + (0.15,)
    footer = dom_weekend.footer + (0.15,)

class dom_holiday(dom):
    """day of month (holiday, indicated by the OFF flag in the holiday file)"""
    fg = _fg
    bg = (0.8,0.8,0.8,_OPACITY)
    header = (0,0,0)
    font = ("Times New Roman", 0, 1)
    
class dom_weekend_holiday(dom_holiday):
    """day of month (weekend & holiday)"""
    bg = (0.8,0.8,0.8,_OPACITY)

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
    frame_thickness = 0.3
    bg = (1,1,1,_OPACITY)
    color_map = ((1,1,1),)*13
    color_map_bg = (((1,1,1,_OPACITY),)*13,((.8,.8,.8,_OPACITY),)*13)
    color_map_fg = (((0,0,0),)*13,((0,0,0),)*13)
    box_shadow = False
    text_shadow = False
