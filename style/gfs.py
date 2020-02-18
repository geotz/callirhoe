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

# --- style.gfs ---

"""module defining Greek Font Society fonts for default style"""

from . import default

# day of week
class dow(default.dow):
    font = "GFS Neohellenic"
    
# day of month
class dom(default.dom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_weekend(default.dom_weekend): 
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_holiday(default.dom_holiday):
    font = ("GFS Bodoni",)
    header_font = footer_font = "GFS Elpis"
    
class dom_weekend_holiday(default.dom_weekend_holiday):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_phantom(default.dom_phantom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_weekend_phantom(default.dom_weekend_phantom):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class dom_multi(default.dom_multi):
    font = ("GFS Bodoni",)
    header_font = footer_font = "GFS Elpis"

class dom_weekend_multi(default.dom_weekend_multi):
    font = "GFS Bodoni"
    header_font = footer_font = "GFS Elpis"

class month(default.month):
    font = ("GFS Artemisia", 0, 1)
