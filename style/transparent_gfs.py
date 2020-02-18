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

# --- style.transparent_gfs ---

"""module defining Greek Font Society fonts for transparent style"""

from . import transparent as base

# day of week
class dow(base.dow):
    font = "GFS Neohellenic"
    
# day of month
class dom(base.dom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_weekend(base.dom_weekend):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_phantom(base.dom_phantom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_weekend_phantom(base.dom_weekend_phantom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_holiday(base.dom_holiday):
    font = ("GFS Bodoni",)
    header_font = footer_font = "GFS Elpis"
    
class dom_weekend_holiday(base.dom_weekend_holiday):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_multi(base.dom_multi):
    font = ("GFS Bodoni",)
    header_font = footer_font = "GFS Elpis"

class dom_weekend_multi(base.dom_weekend_multi):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class month(base.month):
    font = ("GFS Artemisia", 0, 1)
