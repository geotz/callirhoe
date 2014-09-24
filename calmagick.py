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

from callirhoe import extract_parser_args
import optparse

def run_callirhoe(style, w, h, args, outfile):
    subprocess.call(['callirhoe', '-s', style, '--no-footer', '--border', '0', '--paper=-%d:-%d' % (w,h)] + args + [outfile])

# TODO: parse dimensions
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
    parser = optparse.OptionParser(usage="usage: %prog IMAGE [options] [callirhoe-options] [--post-magick IMAGEMAGICK-options]",
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
    parser.add_option("--test",  action="store_true", default=False,
                    help="generate image showing minimum entropy area only, without calendar")
    parser.add_option("--test-rect",  action="store_true", default=False,
                    help="print minimum entropy area in STDOUT as X Y W H, without generating any files")
    parser.add_option("-v", "--verbose",  action="store_true", default=False,
                    help="print progress messages")

    im = optparse.OptionGroup(parser, "ImageMagick Options", "These options determine how ImageMagick is used.")
    im.add_option("--brightness",  type="int", default=10,
                    help="increase/decrease brightness by this (percent) value; "
                    "brightness is decreased on negative overlays [%default]")
    im.add_option("--saturation",  type="int", default=100,
                    help="set saturation of the overlaid area "
                    "to this value (percent) [%default]")
    im.add_option("--edge",  type="float", default=2,
                    help="radius argument for the edge detection algorithm (entropy computation) [%default]")
    im.add_option("--pre-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, before entropy computation")
    im.add_option("--in-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the minimal-entropy area")
    im.add_option("--post-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the final output")
    parser.add_option_group(im)
    return parser

if __name__ == '__main__':
    parser = get_parser()

    magickargs = []
    try:
        m = sys.argv.index('--post-magick')
        magickargs = sys.argv[m+1:]
        del sys.argv[m:]
    except:
        pass

    sys.argv,argv2 = extract_parser_args(sys.argv,parser,2)
    (options,args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
    #        print "Usage: %s BACKGROUNDIMAGE [callirhoe args ...] " % (sys.argv[0])
        sys.exit(0)

    img = args[0]
    base,ext = os.path.splitext(img)

    if options.verbose: print "Extracting image info..."
    #info = subprocess.check_output(['convert', img, '-colorspace', 'gray', '-format', '%w %h %[fx:mean]', 'info:']).split()
    info = subprocess.check_output(['convert', img, '-format', '%w %h', 'info:']).split()
    w,h = map(int, info)
    resize = '%dx%d!' % (options.quantum, options.quantum)
    if options.verbose:
        print "%s %dx%d %dmp" % (img, w, h, int(w*h/1000000.0+0.5))
        print "Calculating image entropy..."
#    pnm_entropy = PNMImage(subprocess.check_output(['convert', img, '-resize', '2500>', '-colorspace', 'HSL', '-channel', 'B', '-separate',
#        '-colorspace', 'Gray', '-edge', str(options.edge), '-scale', resize, '-compress', 'None', 'pnm:-']).splitlines())
#    pnm_entropy = PNMImage(subprocess.check_output(['convert', img, '-scale', '2500>', '-colorspace', 'Gray',
#        '-edge', str(options.edge), '-scale', resize, '-compress', 'None', 'pnm:-']).splitlines())
    pnm_entropy = PNMImage(subprocess.check_output(['convert', img, '-scale', '512>', '(', '+clone',
        '-blur', '0x%d' % options.edge, ')', '-compose', 'minus', '-composite',
        '-colorspace', 'Gray', '-normalize', '-unsharp', '0x5', '-scale', resize, '-normalize', '-compress', 'None', 'pnm:-']).splitlines())

    if options.verbose: print "Fitting... ",
    best = pnm_entropy.fit_rect((options.min_size,options.max_size), options.low_entropy, options.relax)
    if options.verbose: print best

    nw, nh = int(w*best[1]), int(h*best[1])
    dx = int(float(w*best[2])/pnm_entropy.size[0])
    dy = int(float(h*best[3])/pnm_entropy.size[1])
    #print nw, nh, dx, dy

    if options.test:
        subprocess.call(['convert', img, '-region', '%dx%d+%d+%d' % (nw,nh,dx,dy),
            '-negate', base+'-0'+ext])
#        subprocess.call(['convert', img, '-region', '%dx%d+%d+%d' % (nw,nh,dx,dy),
#            '-border', '2', '-bordercolor', 'black', '-border', '1', base+'-0'+ext])

    if options.test_rect:
        print dx, dy, nw, nh

    if options.test or options.test_rect:
        sys.exit(0)

    if options.verbose: print "Measuring luminance... ",
#    pnm_lum = PNMImage(subprocess.check_output(['convert', img, '-colorspace', 'HSL', '-channel', 'B', '-separate',
#        '-colorspace', 'Gray', '-scale', resize, '-compress', 'None', 'pnm:-']).splitlines())
    pnm_lum = PNMImage(subprocess.check_output(['convert', img, '-colorspace', 'Gray',
        '-scale', resize, '-compress', 'None', 'pnm:-']).splitlines())
    luma = pnm_lum.block_avg(*best[2:5])
    #print 'luma =', luma
    negative = luma < options.negative
    if options.verbose: print "DARK" if negative else "LIGHT"


    if options.verbose: print "Generating calendar image (transparent)..."
    run_callirhoe('mono_transparent', nw, nh, argv2, '_transparent_cal.png');

    if options.verbose: print "Composing overlay..."
    overlay = ['(', '-negate', '_transparent_cal.png', ')'] if negative else ['_transparent_cal.png']
    subprocess.call(['convert', img, '-region', '%dx%d+%d+%d' % (nw,nh,dx,dy)] +
        ([] if options.brightness == 0 else ['-brightness-contrast', '%d' % (-options.brightness if negative else options.brightness)]) +
        ([] if options.saturation == 100 else ['-modulate', '100,%d' % options.saturation]) +
        ['-compose', 'over'] +  overlay + ['-geometry', '+%d+%d' % (dx,dy), '-composite'] +
        magickargs + [base+'-0'+ext])
        
#    subprocess.call(['composite', '-gravity', 'center', '(', '-negate', '_transparent_cal.png', ')', img, base+'-1'+ext])
#    print "Composing overlay (blend)..."
#    subprocess.call(['composite', '-blend', '50', '-gravity', 'center', '_transparent.png', img, 'bar2.jpg'])
#    print "Composing overlay (negative blend)..."
#    subprocess.call(['composite', '-blend', '50', '-gravity', 'center', '(', '-negate', '_transparent.png', ')', img, 'bar3.jpg'])

#convert p6.jpg -colorspace HSL -channel B -separate -resize 12x12\! -compress None pnm:-
#convert p1.jpg -colorspace HSL -channel B -separate -edge 2 -resize 12x12! -compress None pnm:-
 
