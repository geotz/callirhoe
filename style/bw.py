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

# --- style.bw ---

# day of week
class dow:
    fg = (.33,.33,.33)
    frame_thickness = 1.0
    frame = (0.8,0.8,0.8)
    font = "Arial"
    
# day of month
class dom:
    bg = (1,1,1)
    frame = (0.8,0.8,0.8)
    frame_thickness = 1.0
    fg = (0.2,0.2,0.2)
    font = "Times New Roman"
    header = (0.5,0.5,0.5)
    footer = header
    header_font = footer_font = "Arial"

class dom_weekend(dom):
    bg = (0.95,0.95,0.95)
    fg = (0,0,0)
    font = ("Times New Roman", 0, 1)

class dom_holiday(dom):
    fg = (0,0,0)
    header = (0,0,0)
    font = ("Times New Roman", 0, 1)
    
class dom_weekend_holiday_style(dom_holiday):
    bg = (0,0,0)

class month:    
    font = ("Times New Roman", 0, 1)
    frame = (0,0,0)
    frame_thickness = 1.0
    bg = (1,1,1)
    color_map = ((1,1,1),)*13
    box_shadow = False
    text_shadow = False
