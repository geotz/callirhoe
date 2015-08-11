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

# --- style.default ---

"""module defining the default style"""

class dow:
    """day of week style"""
    fg = (0,0,1)
    frame_thickness = 0.1
    frame = (0.75,0.75,0.75)
    font = "Arial"
    
class dom:
    """day of month style"""
    bg = (1,1,1)
    frame = (0.75,0.75,0.75)
    frame_thickness = 0.1
    fg = (0.2,0.2,0.2)
    font = "Times New Roman"
    header = (0.5,0.5,0.5)
    footer = header
    header_font = footer_font = "Arial"

class dom_weekend(dom):
    """day of month style (weekend)"""
    bg = (0.7,1,1)
    fg = (0,0,1)

class dom_holiday(dom):
    """day of month (holiday, indicated by the OFF flag in the holiday file)"""
    bg = (0.7,1,1)
    fg = (1,0,0)
    header = (1,0,0)

class dom_weekend_holiday(dom_holiday):
    """day of month (weekend & holiday)"""
    pass

class dom_phantom(dom):
    """day of month (phantom -- belonging to previous/next month)"""
    fg = (0.8,)*3
    header = footer = (0.8,)*3

class dom_weekend_phantom(dom_weekend):
    """day of month (phantom weekend)"""
    fg = (0.8,)*3
    header = footer = (0.8,)*3

class dom_multi(dom):
    """day of month (multi-day holiday)"""
    bg = (0.7,1,1)

class dom_weekend_multi(dom_multi):
    """day of month (weekend in multi-day holiday)"""
    pass

class month:    
    """month style"""
    font = ("Times New Roman", 0, 1)
    frame = (0,0,0)
    frame_thickness = 0.2
    bg = (1,1,1)
    text_shadow = True
    text_shadow_size = 0.2
    box_shadow = True
    box_shadow_size = 2
    color_map_bg = (((.1,.3,.6),)*13,((.1,.5,.6),)*13)
    color_map_fg = (((1,1,1),)*13,((1,1,1),)*13)
