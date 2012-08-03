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

# --- style.screenshot ---

# day of week
class dow:
    fg = (0,0,1)
    frame_thickness = 5.0
    frame = (0,0,0)
    font = "Arial"
    
# day of month
class dom:
    bg = (1,1,1)
    frame = (0.5,0.5,0.5)
    frame_thickness = 5.0
    fg = (0.2,0.2,0.2)
    font = "GFS Bodoni"
    header = (0.5,0.5,0.5)
    footer = header
    header_font = footer_font = "Arial"

class dom_weekend(dom):
    bg = (0.7,1,1)
    fg = (0,0,1)

class dom_holiday(dom):
    fg = (1,0,0)
    header = (1,0,0)
    
class dom_weekend_holiday_style(dom_holiday):
    bg = (0.7,1,1)

from lib.geom import color_mix

class month:    
    font = "GFS Artemisia Bold"
    frame = (0,0,0)
    frame_thickness = 5.0
    bg = (1,1,1)
    winter = (0,0.4,1)
    spring = (0.0,0.5,0.0)
    summer = (1,0.3,0)
    autumn = (0.9,0.9,0)
    color_map = ((0,0,0), winter,
        color_mix(winter,spring,0.66), color_mix(winter,spring,0.33), spring, # april
        color_mix(spring,summer,0.66), color_mix(spring,summer,0.33), summer, # july
        color_mix(summer,autumn,0.66), color_mix(summer,autumn,0.33), autumn, # october
        color_mix(autumn,winter,0.66), color_mix(autumn,winter,0.33)) # december
    text_shadow = True
    box_shadow = True
