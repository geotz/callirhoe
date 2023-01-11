#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012-2015 George M. Tzoumas

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
"""  high quality photo calendar composition using ImageMagick  """
#                                                                 #
# *****************************************************************

import sys
import subprocess
import os.path
import os
import tempfile
import glob
import random
import optparse
import queue
import threading

import lib
from lib.geom import rect_rel_scale

# MAYBE-TODO
# move to python 3?
# check ImageMagick availability/version
# convert input to ImageMagick native format for faster re-access
# report error on parse-float (like atoi())
# abort --range only on KeyboardInterrupt?

_prog_im = os.getenv('CALLIRHOE_IM', 'convert')
"""ImageMagick binary, either 'convert' or env var C{CALLIRHOE_IM}"""

def run_callirhoe(style, size, args, outfile):
    """launch callirhoe to generate a calendar

    @param style: calendar style to use (passes -s option to callirhoe)
    @param size: tuple (I{width},I{height}) for output calendar size (in pixels)
    @param args: (extra) argument list to pass to callirhoe
    @param outfile: output calendar file
    @rtype: subprocess.Popen
    @return: Popen object
    """
    return subprocess.Popen(['callirhoe', '-s', style, '--paper=-%d:-%d' % size] + args + [outfile])

def _bound(x, lower, upper):
    """return the closest number to M{x} that lies in [M{lower,upper}]

    @rtype: type(x)
    """
    if x < lower: return lower
    if x > upper: return upper
    return x

class PNMImage(object):
    """class to represent an PNM grayscale image given in P2 format

    @ivar data: image data as 2-dimensional array (list of lists)
    @ivar size: tuple M{(width,height)} of image dimensions
    @ivar maxval: maximum grayscale value
    @ivar _rsum_cache: used by L{_rsum()} to remember results
    @ivar xsum: 2-dimensional array of running x-sums for each line, used for efficient
    computation of block averages, resulting in M{O(H)} complexity, instead of M{O(W*H)},
    where M{W,H} the image dimensions
    """
    def __init__(self, strlist):
        self.data = [];
        state = 0;
        for i in range(len(strlist)):
            # skip comments
            if strlist[i].startswith(b'#'): continue
            # skip empty lines
            if len(strlist[i]) == 0: continue
            # parse header
            if state == 0:
                if not strlist[i].startswith(b'P2'):
                    raise RuntimeError('invalid PNM image format: %s' % strlist[i])
                state += 1
            # parse size
            elif state == 1:
                w,h = list(map(int,strlist[i].split()))
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
                data = ' '.join([s.decode('utf-8') for s in strlist[i:] if not s.startswith(b'#')])
                intlist = list(map(int,data.split()))
                self.data = [intlist[x:x+w] for x in range(0, len(intlist), w)]
                break

        self._rsum_cache=(-1,-1,0) # y,x,s
#        self.xsum = [map(lambda x: sum(self.data[y][0:x]), range(w+1)) for y in range(0,h)]
        self.xsum = [[self._rsum(y,x) for x in range(w+1)] for y in range(0,h)]

    def _rsum(self,y,x):
        """running sum with cache

        @rtype: int
        """
        if self._rsum_cache[0] == y and self._rsum_cache[1] == x:
            s = self._rsum_cache[2] + self.data[y][x-1]
        else:
            s = sum(self.data[y][0:x])
        self._rsum_cache = (y,x+1,s)
        return s

    def block_avg(self, x, y, szx, szy):
        """returns the average intensity of a block of size M{(szx,szy)} at pos (top-left) M{(x,y)}

        @rtype: float
        """
        return float(sum([(self.xsum[y][x+szx] - self.xsum[y][x]) for y in range(y,y+szy)]))/(szx*szy)

    def lowest_block_avg(self, szx, szy, at_least = 0):
        """returns the M{(szx,szy)}-sized block with intensity as close to M{at_least} as possible
        @rtype: (float,(float,float),(int,int),(int,int))
        @return: R=tuple M({avg, (szx_ratio,szy_ratio), (x,y), (szx,szy))}: R[0] is the
        average intensity of the block found, R[1] is the block size ratio with respect to the whole image,
        R[2] is the block position (top-left) and R[3] is the block size
        """
        w,h = self.size
        best = (self.maxval,(1,1),(0,0),(szx,szy)) # avg, (szx_ratio,szy_ratio), (x,y), (szx,szy)
        for y in range(0,h-szy+1):
            for x in range(0,w-szx+1):
                cur = (self.block_avg(x,y,szx,szy), (float(szx)/w,float(szy)/h), (x,y), (szx,szy))
                if cur[0] < best[0]:
                    best = cur
                    if best[0] <= at_least: return best
        return best

    def fit_rect(self, size_range = (0.333, 0.8), at_least = 7, relax = 0.2, rr = 1.0):
        """find the maximal-area minimal-entropy rectangle within the image

        @param size_range: tuple of smallest and largest rect/photo size ratio

        size measured on the 'best-fit' dimension' if rectangle and photo ratios differ
        @param at_least: early stop of minimization algorithm, when rect of this amount of entropy is found
        @param relax: relax minimum entropy by a factor of (1+M{relax}), so that bigger sizes can be tried

        This is because usuallly minimal entropy is achieved at a minimal-area box.
        @param rr: ratio of ratios

        Calendar rectangle ratio over Photo ratio. If M{r>1} then calendar rectangle, when scaled, fits
        M{x} dimension first. Conversely, if M{r<1}, scaling touches the M{y} dimension first. When M{r=1},
        calendar rectangle can fit perfectly within the photo at 100% size.

        @rtype: (float,(float,float),(int,int),(int,int),float)
        """
        w,h = self.size
        sz_lo = _bound(int(w*size_range[0]+0.5),1,w)
        sz_hi = _bound(int(w*size_range[1]+0.5),1,w)
        szv_range = list(range(sz_lo, sz_hi+1))
        if rr == 1:
            sz_range = list(zip(szv_range, szv_range))
        elif rr > 1:
            sz_range = list(zip(szv_range, [_bound(int(x/rr+0.5),1,w) for x in szv_range]))
        else:
            sz_range = list(zip([_bound(int(x*rr+0.5),1,w) for x in szv_range], szv_range))
        best = self.lowest_block_avg(*sz_range[0])
        # we do not use at_least because non-global minimum, when relaxed, may jump well above threshold
        entropy_thres = max(at_least, best[0]*(1+relax))
        for sz in list(reversed(sz_range))[0:-1]:
            # we do not use at_least because we want the best possible option, for bigger sizes
            cur = self.lowest_block_avg(*sz)
            if cur[0] <= entropy_thres: return cur + (best[0],)
        return best + (best[0],) # avg, (szx_ratio,szy_ratio), (x,y), (szx,szy), best_avg


def get_parser():
    """get the argument parser object

    @rtype: optparse.OptionParser
    """
    parser = optparse.OptionParser(usage="usage: %prog IMAGE [options] [callirhoe-options] [--pre-magick ...] [--in-magick ...] [--post-magick ...]",
           description="""High quality photo calendar composition with automatic minimal-entropy placement.
If IMAGE is a single file, then a calendar of the current month is overlayed. If IMAGE contains wildcards,
then every month is generated according to the --range option, advancing one month for every photo file.
Photos will be reused in a round-robin fashion if more calendar
months are requested.""", version="callirhoe.CalMagick " + lib._version + '\n' + lib._copyright)
    parser.add_option("--outdir", default=".",
                    help="set directory for the output image(s); directory will be created if it does not already exist [%default]")
    parser.add_option("--outfile", default=None,
                    help="set output filename when no --range is requested; by default will use the same name, unless it is going to "
                    "overwrite the input image, in which case suffix '_calmagick' will be added; this option will override --outdir and --format options")
    parser.add_option("--prefix", type="choice", choices=['no','auto','yes'], default='auto',
                    help="set output filename prefix for multiple image output (with --range); 'no' means no prefix will be added, thus the output "
                    "filename order may not be the same, if the input photos are randomized (--shuffle or --sample), also some output files may be overwritten, "
                    "if input photos are reused in round-robin; "
                    "'auto' adds YEAR_MONTH_ prefix only when input photos are randomized or more months than photos are requested; 'yes' will always add prefix [%default]")
    parser.add_option("--quantum", type="int", default=60,
                    help="choose quantization level for entropy computation [%default]")
    parser.add_option("--placement", type="choice", choices="min max N S W E NW NE SW SE center random".split(),
                    default="min", help="choose placement algorithm among {min, max, "
                    "N, S, W, E, NW, NE, SW, SE, center, random} [%default]")
    parser.add_option("--min-size",  type="float", default=None,
                    help="for min/max/random placement: set minimum calendar/photo size ratio [0.333]; for "
                    "N,S,W,E,NW,NE,SW,SE placement: set margin/opposite-margin size ratio [0.05]; for "
                    "center placement it has no effect")
    parser.add_option("--max-size",  type="float", default=0.8,
                    help="set maximum calendar/photo size ratio [%default]")
    parser.add_option("--ratio", default="0",
                    help="set calendar ratio either as a float or as X/Y where X,Y positive integers; if RATIO=0 then photo ratio R is used; note that "
                    "for min/max placement, calendar ratio CR will be equal to the closest number (a/b)*R, where "
                    "a,b integers, and MIN_SIZE <= x/QUANTUM <= MAX_SIZE, where x=b if RATIO < R otherwise x=a; in "
                    "any case 1/QUANTUM <= CR/R <= QUANTUM [%default]")
    parser.add_option("--low-entropy",  type="float", default=7,
                    help="set minimum entropy threshold (0-255) for early termination (0=global minimum) [%default]")
    parser.add_option("--relax",  type="float", default=0.2,
                    help="relax minimum entropy multiplying by 1+RELAX, to allow for bigger sizes [%default]")
    parser.add_option("--negative",  type="float", default=100,
                    help="average luminosity (0-255) threshold of the overlaid area, below which a negative "
                    "overlay is chosen [%default]")
    parser.add_option("--test",  type="choice", choices="none area quant quantimg print crop".split(), default='none',
                    help="test entropy minimization algorithm, without creating any calendar, TEST should be among "
                    "{none, area, quant, quantimg, print, crop}: none=test disabled; "
                    "area=show area in original image; quant=show area in quantizer; "
                    "quantimg=show both quantizer and image; print=print minimum entropy area in STDOUT as W H X Y, "
                    "without generating any files at all; crop=crop selected area [%default]")
    parser.add_option("--alt",  action="store_true", default=False,
                    help="use an alternate entropy computation algorithm; although for most cases it should be no better than the default one, "
                    "for some cases it might produce better results (yet to be verified)")
    parser.add_option("-v", "--verbose",  action="store_true", default=False,
                    help="print progress messages")

    cal = optparse.OptionGroup(parser, "Calendar Options", "These options determine how callirhoe is invoked.")
    cal.add_option("-s", "--style", default="transparent",
                    help="calendar default style [%default]")
    cal.add_option("--range", default=None,
                    help="""set month range for calendar. Format is MONTH/YEAR or MONTH1-MONTH2/YEAR or
MONTH:SPAN/YEAR. If set, these arguments will be expanded (as positional arguments for callirhoe)
and a calendar will be created for
each month separately, for each input photo. Photo files will be globbed by the script
and used in a round-robin fashion if more months are requested. Globbing means that you should
normally enclose the file name in single quotes like '*.jpg' in order to avoid shell expansion.
If less months are requested, then the calendar
making process will terminate without having used all available photos. SPAN=0 will match the number of input
photos.""")
    cal.add_option('-j', "--jobs", type="int", default=1,
                    help="set parallel job count (total number of threads) for the --range iteration; although python "
                    "threads are not true processes, they help running the external programs efficiently [%default]")
    cal.add_option("--sample", type="int", default=None,
                    help="choose SAMPLE random images from the input and use in round-robin fashion (see --range option); if "
                    "SAMPLE=0 then the sample size is chosen to as big as possible, either equal to the month span defined with --range, or "
                    "equal to the total number of available photos")
    cal.add_option("--shuffle", action="store_true", default=False,
                    help="shuffle input images and to use in round-robin fashion (see --range option); "
                    "the sample size is chosen to be equal to the month span defined with --range or equal to "
                    "the total number of available photos (whichever is smaller); this "
                    "is equivalent to specifying --sample=0")
    cal.add_option("--vanilla", action="store_true", default=False,
                    help="suppress default options --no-footer --border=0")
    parser.add_option_group(cal)

    im = optparse.OptionGroup(parser, "ImageMagick Options", "These options determine how ImageMagick is used.")
    im.add_option("--format", default="",
                    help="determines the file extension (without dot!) of the output image files; "
                    "use this option to generate files in a different format than the input, for example "
                    "to preserve quality by generating PNG from JPEG, thus not recompressing")
    im.add_option("--brightness",  type="int", default=10,
                    help="increase/decrease brightness by this (percent) value; "
                    "brightness is decreased on negative overlays [%default]")
    im.add_option("--saturation",  type="int", default=100,
                    help="set saturation of the overlaid area "
                    "to this value (percent) [%default]")
#    im.add_option("--radius",  type="float", default=2,
#                    help="radius for the entropy computation algorithm [%default]")
    im.add_option("--pre-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, before entropy computation; should precede --in-magick and --post-magick")
    im.add_option("--in-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the minimal-entropy area; should precede --post-magick")
    im.add_option("--post-magick",  action="store_true", default=False,
                    help="pass all subsequent arguments to ImageMagick, to be applied on the final output")
    parser.add_option_group(im)
    return parser

def check_parsed_options(options):
    """set (remaining) default values and check validity of various option combinations"""
    if options.min_size is None:
        options.min_size = min(0.333,options.max_size) if options.placement in ['min','max','random'] else min(0.05,options.max_size)
    if options.min_size > options.max_size:
        raise lib.Abort("calmagick: --min-size should not be greater than --max-size")
    if options.sample is not None and not options.range:
        raise lib.Abort("calmagick: --sample requested without --range")
    if options.outfile is not None and options.range:
        raise lib.Abort("calmagick: you cannot specify both --outfile and --range options")
    if options.sample is not None and options.shuffle:
        raise lib.Abort("calmagick: you cannot specify both --shuffle and --sample options")
    if options.shuffle:
        options.sample = 0
    if options.sample is None:
        if options.prefix == 'auto': options.prefix = 'no?' # dirty, isn't it? :)
    else:
        if options.prefix == 'auto': options.prefix = 'yes'
    if options.jobs < 1: options.jobs = 1

def parse_magick_args():
    """extract arguments from command-line that will be passed to ImageMagick

    ImageMagick-specific arguments should be defined between arguments C{--pre-magick},
    C{--in-magick}, C{--post-magick} is this order

    @rtype: [[str,...],[str,...],[str,...]]
    @return: 3-element list of lists containing the [pre,in,post]-options
    """
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

def mktemp(ext=''):
    """get temporary file name with optional extension

    @rtype: str
    """
    f = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    f.close()
    return f.name

def get_outfile(infile, outdir, base_prefix, format, hint=None):
    """get output file name taking into account output directory, format and prefix, avoiding overwriting the input file

    @rtype: str
    """
    if hint:
        outfile = hint
    else:
        head,tail = os.path.split(infile)
        base,ext = os.path.splitext(tail)
        if format: ext = '.' + format
        outfile = os.path.join(outdir,base_prefix+base+ext)
    if os.path.exists(outfile) and os.path.samefile(infile, outfile):
        if hint: raise lib.Abort("calmagick: --outfile same as input, aborting")
        outfile = os.path.join(outdir,base_prefix+base+'_calmagick'+ext)
    return outfile

def _IM_get_image_size(img, args):
    """extract tuple(width,height) from image file using ImageMagick

    @rtype: (int,int)
    """
    info = subprocess.check_output([_prog_im, img] + args + ['-format', '%w %h', 'info:']).split()
    return tuple(map(int, info))

_IM_lum_args = "-colorspace Lab -channel R -separate +channel -set colorspace Gray".split()
"""IM colorspace conversion arguments to extract image luminance"""

def _IM_get_image_luminance(img, args, geometry = None):
    """get average image luminance as a float in [0,255], using ImageMagick

    @rtype: float
    """
    return 255.0*float(subprocess.check_output([_prog_im, img] + args +
            (['-crop', '%dx%d+%d+%d' % geometry] if geometry else []) +
            _IM_lum_args + ['-format', '%[fx:mean]', 'info:']))

_IM_entropy_head = "-scale 262144@>".split()
"""IM args for entropy computation: pre-scaling"""
_IM_entropy_alg = ["-define convolve:scale=! -define morphology:compose=Lighten -morphology Convolve Sobel:>".split(),
                 "( +clone -blur 0x2 ) +swap -compose minus -composite".split()]
"""IM main/alternate entropy computation operator"""
_IM_entropy_tail = "-colorspace Lab -channel R -separate +channel -set colorspace Gray -normalize -scale".split()
"""IM entropy computation final colorspace"""
#_IM_entropy_tail = "-colorspace Lab -channel R -separate +channel -normalize -scale".split()

def _IM_entropy_args(alt=False):
    """IM entropy computation arguments, depending on default or alternate algorithm

    @rtype: [str,...]
    """
    return _IM_entropy_head + _IM_entropy_alg[alt] + _IM_entropy_tail

def _entropy_placement(img, size, args, options, r):
    """get rectangle of minimal/maximal entropy

    @param img: image file
    @param size: image size tuple(I{width,height})
    @param args: ImageMagick pre-processing argument list (see C{--pre-magick})
    @param options: (command-line) options object
    @param r: rectangle ratio, 0=match input ratio
    @rtype: (int,int,int,int)
    @return: IM geometry tuple(I{width,height,x,y})
    """
    w,h = size
    R = float(w)/h
    if r == 0: r = R
    if options.verbose:
        print("Calculating image entropy...")
    qresize = '%dx%d!' % ((options.quantum,)*2)
    pnm_entropy = PNMImage(subprocess.check_output([_prog_im, img] + args + _IM_entropy_args(options.alt) +
    [qresize, '-normalize'] + (['-negate'] if options.placement == 'max' else []) + "-compress None pnm:-".split()).splitlines())

    # find optimal fit
    if options.verbose: print("Fitting... ", end=' ')
    best = pnm_entropy.fit_rect((options.min_size,options.max_size), options.low_entropy, options.relax, r/R)
    if options.verbose:
        print("ent=%0.2f frac=(%0.2f,%0.2f) pos=(%d,%d) bs=(%d,%d) min=%0.2f r=%0.2f" % (
            best[0], best[1][0], best[1][1], best[2][0], best[2][1], best[3][0], best[3][1], best[4], R*best[3][0]/best[3][1]))

    # (W,H,X,Y)
    w,h = size
    geometry = tuple(map(int, (w*best[1][0], h*best[1][1],
                        float(w*best[2][0])/pnm_entropy.size[0],
                        float(h*best[2][1])/pnm_entropy.size[1])))
    return geometry

def _manual_placement(size, options, r):
    """get rectangle of ratio I{r} with user-defined placement (N,S,W,E,NW,NE,SW,SE,center,random)

    @param size: image size tuple(I{width,height})
    @param options: (command-line) options object
    @param r: rectangle ratio, 0=match input ratio
    @rtype: (int,int,int,int)
    @return: IM geometry tuple(I{width,height,x,y})
    """
    w,h = size
    rect = (0, 0, w, h)
    R = float(w)/h
    if r == 0: r = R
    if r == R: # float comparison should succeed here
        fx, fy = 1.0, 1.0
    elif r > R:
        fx,fy = 1.0, R/r
    else:
        fx,fy = r/R, 1.0
    if options.placement == 'random':
        f = random.uniform(options.min_size, options.max_size)
        rect2 = rect_rel_scale(rect, f*fx, f*fy, random.uniform(-1,1), random.uniform(-1,1))
    else:
        ax = ay = 0
        if 'W' in options.placement: ax = -1 + 2.0*options.min_size
        if 'E' in options.placement: ax = 1 - 2.0*options.min_size
        if 'N' in options.placement: ay = -1 + 2.0*options.min_size
        if 'S' in options.placement: ay = 1 - 2.0*options.min_size
        rect2 = rect_rel_scale(rect, options.max_size*fx, options.max_size*fy, ax, ay)
    return tuple(map(int,[rect2[2], rect2[3], rect2[0], rect2[1]]))

_cache = dict() # {'filename': (geometry, is_dark)}
"""cache input photo computed rectangle and luminance, key=filename, value=(geometry,is_dark)"""
_mutex = threading.Lock()
"""mutex for cache access"""

def get_cache(num_photos, num_months):
    """returns a reference to the cache object, or None if caching is disabled

    @rtype: dict
    @note: caching is enabled only when more than 1/6 of photos is going to be re-used
    """
    q,r = divmod(num_months, num_photos)
    if q > 1: return _cache
    if q < 1 or r == 0: return None
    return _cache if (num_photos / r <= 6) else None;

def compose_calendar(img, outimg, options, callirhoe_args, magick_args, stats=None, cache=None):
    """performs calendar composition on a photo image

    @param img: photo file
    @param outimg: output file
    @param options: (command-line) options object
    @param callirhoe_args: extra argument list to pass to callirhoe
    @param magick_args: [pre,in,post]-magick argument list
    @param stats: if not C{None}: tuple(I{current,total}) counting input photos
    @param cache: if cache enabled, points to the cache dictionary
    """
    # get image info (dimensions)
    geometry, dark = None, None
    if cache is not None:
        with _mutex:
            if img in cache:
                geometry, dark = cache[img]
        if options.verbose and geometry:
            if stats: print("[%d/%d]" % stats, end=' ')
            print("Reusing image info from cache...", geometry, "DARK" if dark else "LIGHT")

    if geometry is None:
        if options.verbose:
            if stats: print("[%d/%d]" % stats, end=' ')
            print("Extracting image info...")
        w,h = _IM_get_image_size(img, magick_args[0])
        qresize = '%dx%d!' % ((options.quantum,)*2)
        if options.verbose:
            print("%s %dx%d %dmp R=%0.2f" % (img, w, h, int(w*h/1000000.0+0.5), float(w)/h))

        if '/' in options.ratio:
            tmp = options.ratio.split('/')
            calratio = float(lib.atoi(tmp[0],1))/lib.atoi(tmp[1],1)
        else:
            calratio = float(options.ratio)
        if options.placement == 'min' or options.placement == 'max':
            geometry = _entropy_placement(img, (w,h), magick_args[0], options, calratio)
        else:
            geometry = _manual_placement((w,h), options, calratio)

    if options.test != 'none':
        if options.test == 'area':
            subprocess.call([_prog_im, img] + magick_args[0] + ['-region', '%dx%d+%d+%d' % geometry,
                '-negate', outimg])
        elif options.test == 'quant':
            subprocess.call([_prog_im, img] + magick_args[0] + _IM_entropy_args(options.alt) +
            [qresize, '-normalize', '-scale', '%dx%d!' % (w,h), '-region', '%dx%d+%d+%d' % geometry,
                '-negate', outimg])
        elif options.test == 'quantimg':
            subprocess.call([_prog_im, img] + magick_args[0] + _IM_entropy_args(options.alt) +
            [qresize, '-normalize', '-scale', '%dx%d!' % (w,h),
                '-compose', 'multiply', img, '-composite', '-region', '%dx%d+%d+%d' % geometry,
                '-negate', outimg])
        elif options.test == 'print':
            print(' '.join(map(str,geometry)))
        elif options.test == 'crop':
            subprocess.call([_prog_im, img] + magick_args[0] + ['-crop', '%dx%d+%d+%d' % geometry,
                outimg])
        return

    # generate callirhoe calendar
    if options.verbose: print("Generating calendar image (%s) ... [&]" % options.style)
    if not options.vanilla: callirhoe_args = callirhoe_args + ['--no-footer', '--border=0']
    calimg = mktemp('.png')
    try:
        pcal = run_callirhoe(options.style, geometry[0:2], callirhoe_args, calimg)

        if dark is None:
            # measure luminance
            if options.verbose: print("Measuring luminance...", end=' ')
            if options.negative > 0 and options.negative < 255:
                luma = _IM_get_image_luminance(img, magick_args[0], geometry)
                if options.verbose: print("(%s)" % luma, end=' ')
            else:
                luma = 255 - options.negative
            dark = luma < options.negative
            if options.verbose: print("DARK" if dark else "LIGHT")
            if cache is not None:
                with _mutex:
                    cache[img] = (geometry, dark)

        pcal.wait()
        if pcal.returncode != 0: raise RuntimeError("calmagick: calendar creation failed")

        # perform final composition
        if options.verbose: print("Composing overlay (%s)..." % outimg)
        overlay = ['(', '-negate', calimg, ')'] if dark else [calimg]
        subprocess.call([_prog_im, img] + magick_args[0] + ['-region', '%dx%d+%d+%d' % geometry] +
            ([] if options.brightness == 0 else ['-brightness-contrast', '%d' % (-options.brightness if dark else options.brightness)]) +
            ([] if options.saturation == 100 else ['-modulate', '100,%d' % options.saturation]) + magick_args[1] +
            ['-compose', 'over'] +  overlay + ['-geometry', '+%d+%d' % geometry[2:], '-composite'] +
            magick_args[2] + [outimg])
    finally:
        os.remove(calimg)

def parse_range(s,hint=None):
    """returns list of (I{Month,Year}) tuples for a given range

    @param s: range string in format I{Month1-Month2/Year} or I{Month:Span/Year}
    @param hint: span value to be used, when M{Span=0}
    @rtype: [(int,int),...]
    @return: list of (I{Month,Year}) tuples for every month specified
    """
    if '/' in s:
        t = s.split('/')
        month,span = lib.parse_month_range(t[0])
        if hint and span == 0: span = hint
        year = lib.parse_year(t[1])
        margs = []
        for m in range(span):
            margs += [(month,year)]
            month += 1
            if month > 12: month = 1; year += 1
        return margs
    else:
        raise lib.Abort("calmagick: invalid range format '%s'" % options.range)

def range_worker(q,ev,i):
    """worker thread for a (I{Month,Year}) tuple

    @param ev: Event used to consume remaining items in case of error
    @param q: Queue object to consume items from
    @param i: Thread number
    """
    while True:
        if ev.is_set():
            q.get()
            q.task_done()
        else:
            item = q.get()
            try:
                compose_calendar(*item)
            except Exception as e:
                print("Exception in Thread-%d: %s" % (i,e.args), file=sys.stderr)
                ev.set()
            finally:
                q.task_done()

def main_program():
    """this is the main program routine

    Parses options, and calls C{compose_calendar()} the appropriate number of times,
    possibly by multiple threads (if requested by user)
    """
    parser = get_parser()

    magick_args = parse_magick_args()
    sys.argv,argv2 = lib.extract_parser_args(sys.argv,parser,2)
    (options,args) = parser.parse_args()
    check_parsed_options(options)

    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    if not os.path.isdir(options.outdir):
        # this way we get an exception if outdir exists and is a normal file
        os.mkdir(options.outdir)

    if options.range:
        flist = sorted(glob.glob(args[0]))
        mrange = parse_range(options.range,hint=len(flist))
        if options.verbose: print("Composing %d photos..." % len(mrange))
        if options.sample is not None:
            flist = random.sample(flist, options.sample if options.sample else min(len(mrange),len(flist)))
        nf = len(flist)
        if nf > 0:
            if len(mrange) > nf and options.prefix == 'no?': options.prefix = 'yes'
            if options.jobs > 1:
                q = queue.Queue()
                ev = threading.Event()
                for i in range(options.jobs):
                     t = threading.Thread(target=range_worker,args=(q,ev,i))
                     t.daemon = True
                     t.start()

            cache = get_cache(nf, len(mrange));
            for i in range(len(mrange)):
                img = flist[i % nf]
                m,y = mrange[i]
                prefix = '' if options.prefix.startswith('no') else '%04d-%02d_' % (y,m)
                outimg = get_outfile(img,options.outdir,prefix,options.format)
                args = (img, outimg, options, [str(m), str(y)] + argv2, magick_args,
                        (i+1,len(mrange)), cache)
                if options.jobs > 1: q.put(args)
                else: compose_calendar(*args)

            if options.jobs > 1: q.join()
    else:
        img = args[0]
        if not os.path.isfile(img):
            raise lib.Abort("calmagick: input image '%s' does not exist" % img)
        outimg = get_outfile(img,options.outdir,'',options.format,options.outfile)
        compose_calendar(img, outimg, options, argv2, magick_args)

if __name__ == '__main__':
    try:
        main_program()
    except lib.Abort as e:
        sys.exit(e.args[0])
