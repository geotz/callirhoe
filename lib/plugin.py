# -*- coding: utf-8 -*-

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

# *****************************************
#                                         #
#        plugin handling routines         #
#                                         #
# *****************************************

import sys
import os.path
import glob

def available_files(parent, dir, fmatch = ""):
    good = False
    res = []
    pattern = parent + "/" + dir + "/*.py"
    for x in glob.glob(pattern):
        basex = os.path.basename(x)
        if basex == "__init__.py": good = True
        elif basex.startswith('_'):
            # ignore files aimed for internal use
            # safer than [a-z]-style matching...
            continue
        else: 
            base = os.path.splitext(basex)[0]
            if base and ((not fmatch) or (fmatch == base)): res.append((base,parent))
    return res if good else []

def plugin_list(cat):
    return available_files(plugin_path[0], cat) + available_files(plugin_path[1], cat)

# cat = lang   (category)
# longcat = language
# longcat2 = languages
# listopt = --list-lang
# preset = "EN"

plugin_path = [ os.path.expanduser("~/.callirhoe"), sys.path[0] if sys.path[0] else "." ]
