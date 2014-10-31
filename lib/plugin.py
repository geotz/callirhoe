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
import pkg_resources

def glob(path, pattern):
"""
 Internal function that scans the given path and subpaths for .py files
"""
    tmplist = pkg_resources.resource_listdir("__main__", "/"+path)
    filelist = []
    for i in tmplist:
        if i == "":
            continue
        if pkg_resources.resource_isdir("__main__", "/"+path+"/"+i):
            filelist.extend(glob(path+"/"+i, pattern))
        else:
            if i.lower()[-3:] == pattern.lower():
                name = path+"/"+i
                filelist.append(name)
    return filelist

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
    for x in glob(dir,".py"):
        basex = os.path.basename(x)
        if basex == "__init__.py": good = True
        elif basex.startswith('_'):
            # ignore files aimed for internal use
            # safer than [a-z]-style matching...
            continue
        else:
            base = os.path.splitext(basex)[0]
            if base and ((not fmatch) or (fmatch == base)): res.append((base,"/"+dir+parent))
    return res if good else []

def plugin_list(cat):
    """return a sequence of available plugins, using L{available_files()} and L{get_plugin_paths()}

    @rtype: [str,...]
    """
    return available_files("../", cat)

# cat = lang   (category)
# longcat = language
# longcat2 = languages
# listopt = --list-lang
# preset = "EN"
