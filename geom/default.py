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

# --- geom.default ---

"""module defining the default geometry"""

class dom:
    """day of month geometry"""
    size = (0.5,0.5,0.8,0.5)   # short 0-1, long 2-3
    mw_split = (0.7,0.2)
    
    header_size = footer_size = (0.8,0.1)
    header_align = 0.15
    footer_align = 0.15
    hf_hsplit = (0.33,0.1)
    hf_vsplit = (0.5,0.4)
    
class month:
    """month geometry"""
    symmetric = False
    sloppy_rot = 0
    sloppy_dx = 0
    sloppy_dy = 0
    padding = 1.5

#class page:
