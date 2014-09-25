#!/usr/bin/env python2.7
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

# *****************************************************************
#                                                                 #
"""  high quality photo calendar composition using Imagemagick  """
#                                                                 #
# *****************************************************************

import sys
import subprocess
import os.path

from callirhoe import extract_parser_args, parse_month_range, parse_year
import optparse

def run_callirhoe(style, w, h, args, outfile):
    if subprocess.call(['callirhoe', '-s', style, '--paper=-%d:-%d' % (w,h)] + args + [outfile]):
        sys.exit("calmagick: calendar creation failed")

class PNMImage(object):
    def __init__(self, strlist):
        self.data = [];
        state = 0;
        for i in range(len(strlist)):
            # skip comments
            if strlist[i].startswith('#'): continue
            # parse header
            if state == 0:
                if not strlist[i].startswith('P2'):
                    raise RuntimeError('invalid PNM image format: %s' % strlist[i])
                state += 1
            # parse size
            elif state == 1:
                w,h = map(int,strlist[i].split())
                if w != h:
                    raise RuntimeError('non-square PNM image')
                self.size = (w,h)
                state += 1
            # parse max value
            elif state == 2:
                self.maxval = int(strlist[i])
                state += 1
            # bitmap
            else:
                data = ' '.join(filter(lambda s: not s.startswith('#'), strlist[i:]))
                intlist = map(int,data.split())
                self.data = [intlist[x:x+w] for x in range(0, len(intlist), w)]
                break

        self.xsum = [map(lambda x: sum(self.data[y][0:x]), range(w+1)) for y in range(0,h)]

    def block_avg(self, x, y, sz):
        return float(sum([(self.xsum[y][x+sz] - self.xsum[y][x]) for y in range(y,y+sz)]))/(sz*sz)

    def lowest_block_avg(self, sz, at_least = 0):
        best = (self.maxval,1,0,0,sz) # avg, sz_ratio, x, y, sz
        w,h = self.size
        for y in range(0,h-sz+1):
            for x in range(0,w-sz+1):
                cur = (self.block_avg(x,y,sz), float(sz)/w, x, y, sz)
                if cur[0] < best[0]:
                    best = cur
                    if best[0] <= at_least: return best
        return best

    def fit_rect(self, size_range = (0.333, 0.8), at_least = 7, relax = 0.2):
        w,h = self.size
        sz_range = (int(w*size_range[0]+0.5), int(w*size_range[1]+0.5))
        best = self.lowest_block_avg(sz_range[0], at_least)
        for sz in range(sz_range[1],sz_range[0],-1):
            cur = self.lowest_block_avg(sz, at_least)
            if cur[0] <= max(at_least, best[0]*(1+relax)): return cur + (best[0],)
        return best + (best[0],) # avg, sz_ratio, x, y, sz, best_avg

_version = "0.1.0"

def get_parser():
    """get the argument parser object"""
    parser = optparse.OptionParser(usage="usage: %prog IMAGE [options] [callirhoe-options] [--pre-magick ...] [--in-magick ...] [--post-magick ...]",
           description="High quality photo calendar composition with automatic minimal-entropy placement. "
           "If IMAGE is a single file, then a calendar of the current month is overlayed. If IMAGE is a directory, "
           "then every month is generated starting from January of the current year (unless otherwise specified), "
           "advancing one month for every photo in the IMAGE directory. "
           "Photos will be reused in a round-robin fashion if more calendar "
           "months are requested.", version="calmagick " + _version)
    parser.add_option("--quantum", type="int", default=60,
                    help="choose quantization level for entropy computation [%default]")
    parser.add_option("--min-size",  type="float", default=0.333,
                    help="set minimum calendar/photo size ratio [%default]")
    parser.add_option("--max-size",  type="float", default=0.8,
                    help="set maximum calendar/photo size ratio [%default]")
    parser.add_option("--low-entropy",  type="float", default=7,
                    help="set minimum entropy threshold (0-255) for early termination (0=global minimum) [%default]")
    parser.add_option("--relax",  type="float", default=0.2,
                    help="relax minimum entropy multiplying by 1+RELAX, to allow for bigger sizes [%default]")
    parser.add_option("--negative",  type="float", default=100,
                    help="average luminosity (0-255) threshold of the overlaid area, below which a negative "
                    "overlay is chosen [%default]")
    parser.add_option("--test",  type="int", default=0,
                    help="test entropy minimization algorithm, without creating any calendar: 0=test disabled, "
                    "1=show area in original image, 2=show area in quantizer, 3=print minimum entropy area in STDOUT as X Y W H, "
                    "without generating any files at all [%default]")
    parser.add_option("-v", "--verbose",  action="store_true", default=False,
                    help="print progress messages")

    cal = optparse.OptionGroup(parser, "Calendar Options", "These options determine how callirhoe is invoked.")
    cal.add_option("-s", "--style", default="transparent",
                    help="calendar default style [%default]")
    cal.add_option("--range", default=None,
                    help="set month range for calendar. Format is MONTH/YEAR or MONTH1-MONTH2/YEAR or "
                    "MONTH:SPAN/YEAR. If set, these arguments will be expanded (as positional arguments for callirhoe) "
                    "and a calendar will be created for "
                    "each month separately, for each input photo. Photo files will be used in a round-robin "
                    "fashion if more months are requested. If less months are requested, then the calendar "
                    "making process will terminate without having used all available photos.")
    cal.add_option("--vanilla", action="store_true", default=False,
                    help="suppress default options --no-footer --border=0")
    parser.add_option_group(cal)

    im = optparse.OptionGroup(parser, "ImageMagick Options", "These options determine how ImageMagick is used.")
    im.add_option("--brightness",  type="int", default=10,
                    help="increase/decrease brightness by this (percent) value; "
                    "brightness is decreased on negative overlays [%default]")
    im.add_option("--saturation",  type="int", default=100,
                    help="set saturation of the overlaid area "
                    "to this value (percent) [%default]")
    im.add_option("--radius",  type="float", default=2,
                    help="radius for the entropy computation algorithm [%default]")
    im.add_option("--pre-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, before entropy computation; should precede --in-magick and --post-magick")
    im.add_option("--in-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the minimal-entropy area; should precede --post-magick")
    im.add_option("--post-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the final output")
    parser.add_option_group(im)
    return parser

def parse_magick_args():
    magickargs = [[],[],[]]
    try:
        m = sys.argv.index('--post-magick')
        magickargs[2] = sys.argv[m+1:]
        del sys.argv[m:]
    except:
        pass
    try:
        m = sys.argv.index('--in-magick')
        magickargs[1] = sys.argv[m+1:]
        del sys.argv[m:]
    except:
        pass
    try:
        m = sys.argv.index('--pre-magick')
        magickargs[0] = sys.argv[m+1:]
        del sys.argv[m:]
    except:
        pass
    if ('--post-magick' in magickargs[2] or '--in-magick' in magickargs[2] or
        '--pre-magick' in magickargs[2] or '--in-magick' in magickargs[1] or
        '--pre-magick' in magickargs[1] or '--pre-magick' in magickargs[0]):
            parser.print_help()
            sys.exit(0)
    return magickargs

if __name__ == '__main__':
    parser = get_parser()

    magickargs = parse_magick_args()
    sys.argv,argv2 = extract_parser_args(sys.argv,parser,2)
    (options,args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    if options.range:
        if '/' in options.range:
            t = options.range.split('/')
            month,span = parse_month_range(t[0])
            year = parse_year(t[1])
            margs = []
            for m in xrange(span):
                margs += [(month,year)]
                month += 1
                if month > 12: month = 1; year += 1
            print margs
            raise NotImplementedError('This feature is still work-in-progress.')
        else:
            sys.exit("Invalid range format '%s'." % options.range)

    img = args[0]
    base,ext = os.path.splitext(img)

    if options.verbose: print "Extracting image info..."
    info = subprocess.check_output(['convert', img, '-format', '%w %h', 'info:']).split()
    w,h = map(int, info)
    resize = '%dx%d!' % (options.quantum, options.quantum)
    if options.verbose:
        print "%s %dx%d %dmp" % (img, w, h, int(w*h/1000000.0+0.5))
        print "Calculating image entropy..."
    pnm_entropy = PNMImage(subprocess.check_output(['convert', img, '-scale', '512>', '(', '+clone',
        '-blur', '0x%d' % options.radius, ')', '-compose', 'minus', '-composite',
        '-colorspace', 'Gray', '-normalize', '-unsharp', '0x5', '-scale', resize, '-normalize', '-compress', 'None', 'pnm:-']).splitlines())

    if options.verbose: print "Fitting... ",
    best = pnm_entropy.fit_rect((options.min_size,options.max_size), options.low_entropy, options.relax)
    if options.verbose: print best

    nw, nh = int(w*best[1]), int(h*best[1])
    dx = int(float(w*best[2])/pnm_entropy.size[0])
    dy = int(float(h*best[3])/pnm_entropy.size[1])
    #print nw, nh, dx, dy

    if options.test == 1:
        subprocess.call(['convert', img, '-region', '%dx%d+%d+%d' % (nw,nh,dx,dy),
            '-negate', base+'-0'+ext])
    if options.test == 2:
        subprocess.call(['convert', img, '-scale', '512>', '(', '+clone',
        '-blur', '0x%d' % options.radius, ')', '-compose', 'minus', '-composite',
        '-colorspace', 'Gray', '-normalize', '-unsharp', '0x5', '-scale', resize, '-normalize',
        '-scale', '%dx%d!' % (w,h), '-region', '%dx%d+%d+%d' % (nw,nh,dx,dy),
            '-negate', base+'-0'+ext])
    elif options.test == 3:
        print dx, dy, nw, nh

    if options.test: sys.exit(0)

    if options.verbose: print "Measuring luminance... ",
    pnm_lum = PNMImage(subprocess.check_output(['convert', img, '-colorspace', 'Gray',
        '-scale', resize, '-compress', 'None', 'pnm:-']).splitlines())
    luma = pnm_lum.block_avg(*best[2:5])
    #print 'luma =', luma
    negative = luma < options.negative
    if options.verbose: print "DARK" if negative else "LIGHT"


    if options.verbose: print "Generating calendar image (transparent)..."
    if not options.vanilla: argv2.extend(['--no-footer', '--border=0'])
    run_callirhoe(options.style, nw, nh, argv2, '_transparent_cal.png');

    if options.verbose: print "Composing overlay..."
    overlay = ['(', '-negate', '_transparent_cal.png', ')'] if negative else ['_transparent_cal.png']
    subprocess.call(['convert', img] + magickargs[0] + ['-region', '%dx%d+%d+%d' % (nw,nh,dx,dy)] +
        ([] if options.brightness == 0 else ['-brightness-contrast', '%d' % (-options.brightness if negative else options.brightness)]) +
        ([] if options.saturation == 100 else ['-modulate', '100,%d' % options.saturation]) + magickargs[1] +
        ['-compose', 'over'] +  overlay + ['-geometry', '+%d+%d' % (dx,dy), '-composite'] +
        magickargs[2] + [base+'-0'+ext])
        
