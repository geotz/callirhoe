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

# --- style.bw_transparent ---

"""module defining the black & white transparent style"""

import bw as base

_OPACITY = 0.1

class dow(base.dow):
    pass
    
class dom(base.dom):
    bg = (1,1,1,_OPACITY)

class dom_weekend(base.dom):
    bg = (0.95,0.95,0.95,_OPACITY)

class dom_holiday(base.dom_holiday):
    """day of month (holiday, indicated by the OFF flag in the holiday file)"""
    bg = (0.95,0.95,0.95,_OPACITY)
    
class dom_weekend_holiday(base.dom_weekend_holiday):
    bg = (0.95,0.95,0.95,_OPACITY)

class dom_multi(base.dom_multi):
    pass

class dom_weekend_multi(base.dom_weekend_multi):
    pass

class month(base.month):    
    bg = (1,1,1,_OPACITY)
    color_map_bg = (((1,1,1,_OPACITY),)*13,((.8,.8,.8,_OPACITY),)*13)
