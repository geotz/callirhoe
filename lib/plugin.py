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
"""        plugin handling routines     """
#                                         #
# *****************************************

import sys
import os.path
import glob

try:
    import resources
except:
    resources = None

def available_files(parent, dir, fmatch = None):
    """find parent/dir/*.py files to be used for plugins

    @rtype: [str,...]
    @note:
           1. __init__.py should exist
           2. files starting with underscore are ignored
           3. if fnmatch is defined (base name), it matches a single file
    """
    good = False
    res = []
    pattern = parent + "/" + dir + "/*.py"
    for x in glob.glob(pattern) if not parent.startswith('resource:') else resources.resource_list[dir]:
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
    """return a sequence of available plugins, using L{available_files()} and L{get_plugin_paths()}

    @rtype: [str,...]
    """
    plugin_paths = get_plugin_paths()
    result = []
    for path in plugin_paths:
        result += available_files(path, cat)
    return result

# cat = lang   (category)
# longcat = language
# longcat2 = languages
# listopt = --list-lang
# preset = "EN"

def get_plugin_paths():
    """return the plugin search paths

    @rtype: [str,str,..]
    """
    result = [ os.path.expanduser("~/.callirhoe"), sys.path[0] if sys.path[0] else "." ]
    if resources:
        result.append("resource:")
    return result
