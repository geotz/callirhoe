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
import os
import tempfile
import glob
import random
import optparse
import Queue
import threading

from callirhoe import extract_parser_args, parse_month_range, parse_year, itoa, Abort
from lib.geom import rect_rel_scale

# TODO:
# epydoc
# cache stuff when --sample is used and more than 10% reuse
# move to python 3

# MAYBE-TODO
# check ImageMagick availability/version
# convert input to ImageMagick native format for faster re-access
# report error on parse-float (like itoa())
# abort --range only on KeyboardInterrupt?

_version = "0.4.0"
_prog_im = os.getenv('CALLIRHOE_IM', 'convert')

def run_callirhoe(style, w, h, args, outfile):
    return subprocess.Popen(['callirhoe', '-s', style, '--paper=-%d:-%d' % (w,h)] + args + [outfile])

def _bound(x, lower_bound, upper_bound):
    if x < lower_bound: return lower_bound
    if x > upper_bound: return upper_bound
    return x

class PNMImage(object):
    def __init__(self, strlist):
        self.data = [];
        state = 0;
        for i in range(len(strlist)):
            # skip comments
            if strlist[i].startswith('#'): continue
            # skip empty lines
            if len(strlist[i]) == 0: continue
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

    def block_avg(self, x, y, szx, szy):
        return float(sum([(self.xsum[y][x+szx] - self.xsum[y][x]) for y in range(y,y+szy)]))/(szx*szy)

    def lowest_block_avg(self, szx, szy, at_least = 0):
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
        w,h = self.size
        sz_lo = _bound(int(w*size_range[0]+0.5),1,w)
        sz_hi = _bound(int(w*size_range[1]+0.5),1,w)
        szv_range = range(sz_lo, sz_hi+1)
        if rr == 1:
            sz_range = zip(szv_range, szv_range)
        elif rr > 1:
            sz_range = zip(szv_range, map(lambda x: _bound(int(x/rr+0.5),1,w), szv_range))
        else:
            sz_range = zip(map(lambda x: _bound(int(x*rr+0.5),1,w), szv_range), szv_range)
        best = self.lowest_block_avg(*sz_range[0])
        # we do not use at_least because non-global minimum, when relaxed, may jump well above threshold
        entropy_thres = max(at_least, best[0]*(1+relax))
        for sz in list(reversed(sz_range))[0:-1]:
            # we do not use at_least because we want the best possible option, for bigger sizes
            cur = self.lowest_block_avg(*sz)
            if cur[0] <= entropy_thres: return cur + (best[0],)
        return best + (best[0],) # avg, sz_ratio, x, y, sz, best_avg


def get_parser():
    """get the argument parser object"""
    parser = optparse.OptionParser(usage="usage: %prog IMAGE [options] [callirhoe-options] [--pre-magick ...] [--in-magick ...] [--post-magick ...]",
           description="""High quality photo calendar composition with automatic minimal-entropy placement.
If IMAGE is a single file, then a calendar of the current month is overlayed. If IMAGE contains wildcards,
then every month is generated according to the --range option, advancing one month for every photo file.
Photos will be reused in a round-robin fashion if more calendar
months are requested.""", version="callirhoe.CalMagick " + _version)
    parser.add_option("--outdir", default=".",
                    help="set directory for the output image(s); directory will be created if it does not already exist [%default]")
    parser.add_option("--outfile", default=None,
                    help="set output filename when no --range is requested; by default will use the same name, unless it is going to "
                    "overwrite the input image, in which case suffix '_calmagick' will be added; this option will override --outdir and --format options")
    parser.add_option("--prefix", type="choice", choices=['no','auto','yes'], default='auto',
                    help="set output filename prefix for multiple image output (with --range); 'no' means no prefix will be added, thus the output "
                    "filename order may not be the same, if the input photos are randomized (--shuffle or --sample); "
                    "'auto' adds YEAR_MONTH_ prefix only when input photos are randomized; 'yes' will always add prefix [%default]")
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
                    "SAMPLE=0 then the sample size is chosen to be equal to the month span defined with --range")
    cal.add_option("--shuffle", action="store_true", default=False,
                    help="shuffle input images and to use in round-robin fashion (see --range option); "
                    "the sample size is chosen to be equal to the month span defined with --range; this "
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
    if options.min_size is None:
        options.min_size = 0.333 if options.placement in ['min','max','random'] else 0.05
    if options.sample is not None and not options.range:
        raise Abort("calmagick: --sample requested without --range")
    if options.outfile is not None and options.range:
        raise Abort("calmagick: you cannot specify both --outfile and --range options")
    if options.sample is not None and options.shuffle:
        raise Abort("calmagick: you cannot specify both --shuffle and --sample options")
    if options.shuffle:
        options.sample = 0
    if options.sample is None:
        if options.prefix == 'auto': options.prefix = 'no'
    else:
        if options.prefix == 'auto': options.prefix = 'yes'
    if options.jobs < 1: options.jobs = 1

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

def mktemp(ext=''):
    f = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    f.close()
    return f.name

def get_outfile(infile, outdir, base_prefix, format, hint=None):
    if hint:
        outfile = hint
    else:
        head,tail = os.path.split(infile)
        base,ext = os.path.splitext(tail)
        if format: ext = '.' + format
        outfile = os.path.join(outdir,base_prefix+base+ext)
    if os.path.exists(outfile) and os.path.samefile(infile, outfile):
        if hint: raise Abort("calmagick: --outfile same as input, aborting")
        outfile = os.path.join(outdir,base_prefix+base+'_calmagick'+ext)
    return outfile

def _get_image_size(img, args):
    info = subprocess.check_output([_prog_im, img] + args + ['-format', '%w %h', 'info:']).split()
    return tuple(map(int, info))

_lum_args = "-colorspace Lab -channel R -separate +channel -set colorspace Gray".split()
def _get_image_luminance(img, args, geometry = None):
    return 255.0*float(subprocess.check_output([_prog_im, img] + args +
            (['-crop', '%dx%d+%d+%d' % geometry] if geometry else []) +
            _lum_args + ['-format', '%[fx:mean]', 'info:']))

_entropy_head = "-scale 262144@>".split()
_entropy_alg = ["-define convolve:scale=! -define morphology:compose=Lighten -morphology Convolve Sobel:>".split(),
                 "( +clone -blur 0x2 ) +swap -compose minus -composite".split()]
_entropy_tail = "-colorspace Lab -channel R -separate +channel -set colorspace Gray -normalize -scale".split()
#_entropy_tail = "-colorspace Lab -channel R -separate +channel -normalize -scale".split()

def entropy_args(alt=False):
    return _entropy_head + _entropy_alg[alt] + _entropy_tail

def _entropy_placement(img, size, args, options, r):
    w,h = size
    R = float(w)/h
    if r == 0: r = R
    if options.verbose:
        print "Calculating image entropy..."
    qresize = '%dx%d!' % ((options.quantum,)*2)
    pnm_entropy = PNMImage(subprocess.check_output([_prog_im, img] + args + entropy_args(options.alt) +
    [qresize, '-normalize'] + (['-negate'] if options.placement == 'max' else []) + "-compress None pnm:-".split()).splitlines())

    # find optimal fit
    if options.verbose: print "Fitting... ",
    best = pnm_entropy.fit_rect((options.min_size,options.max_size), options.low_entropy, options.relax, r/R)
    if options.verbose:
        print "ent=%0.2f frac=(%0.2f,%0.2f) pos=(%d,%d) bs=(%d,%d) min=%0.2f r=%0.2f" % (
            best[0], best[1][0], best[1][1], best[2][0], best[2][1], best[3][0], best[3][1], best[4], R*best[3][0]/best[3][1])

    # (W,H,X,Y)
    w,h = size
    geometry = tuple(map(int, (w*best[1][0], h*best[1][1],
                        float(w*best[2][0])/pnm_entropy.size[0],
                        float(h*best[2][1])/pnm_entropy.size[1])))
    return geometry

def _manual_placement(size, options, r):
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

def compose_calendar(img, outimg, options, callirhoe_args, magick_args, stats=None):
    # get image info (dimensions)
    if options.verbose:
        if stats: print "[%d/%d]" % stats,
        print "Extracting image info..."
    w,h = _get_image_size(img, magick_args[0])
    qresize = '%dx%d!' % ((options.quantum,)*2)
    if options.verbose:
        print "%s %dx%d %dmp R=%0.2f" % (img, w, h, int(w*h/1000000.0+0.5), float(w)/h)

    if '/' in options.ratio:
        tmp = options.ratio.split('/')
        calratio = float(itoa(tmp[0],1))/itoa(tmp[1],1)
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
            subprocess.call([_prog_im, img] + magick_args[0] + entropy_args(options.alt) +
            [qresize, '-normalize', '-scale', '%dx%d!' % (w,h), '-region', '%dx%d+%d+%d' % geometry,
                '-negate', outimg])
        elif options.test == 'quantimg':
            subprocess.call([_prog_im, img] + magick_args[0] + entropy_args(options.alt) +
            [qresize, '-normalize', '-scale', '%dx%d!' % (w,h),
                '-compose', 'multiply', img, '-composite', '-region', '%dx%d+%d+%d' % geometry,
                '-negate', outimg])
        elif options.test == 'print':
            print ' '.join(map(str,geometry))
        elif options.test == 'crop':
            subprocess.call([_prog_im, img] + magick_args[0] + ['-crop', '%dx%d+%d+%d' % geometry,
                outimg])
        return

    # generate callirhoe calendar
    if options.verbose: print "Generating calendar image (%s) ... [&]" % options.style
    if not options.vanilla: callirhoe_args = callirhoe_args + ['--no-footer', '--border=0']
    calimg = mktemp('.png')
    try:
        pcal = run_callirhoe(options.style, geometry[0], geometry[1], callirhoe_args, calimg)

        # measure luminance
        if options.verbose: print "Measuring luminance...",
        if options.negative > 0 and options.negative < 255:
            luma = _get_image_luminance(img, magick_args[0], geometry)
            if options.verbose: print "(%s)" % luma,
        else:
            luma = 255 - options.negative
        dark = luma < options.negative
        if options.verbose: print "DARK" if dark else "LIGHT"
        pcal.wait()
        if pcal.returncode != 0: raise RuntimeError("calmagick: calendar creation failed")

        # perform final composition
        if options.verbose: print "Composing overlay (%s)..." % outimg
        overlay = ['(', '-negate', calimg, ')'] if dark else [calimg]
        subprocess.call([_prog_im, img] + magick_args[0] + ['-region', '%dx%d+%d+%d' % geometry] +
            ([] if options.brightness == 0 else ['-brightness-contrast', '%d' % (-options.brightness if dark else options.brightness)]) +
            ([] if options.saturation == 100 else ['-modulate', '100,%d' % options.saturation]) + magick_args[1] +
            ['-compose', 'over'] +  overlay + ['-geometry', '+%d+%d' % geometry[2:], '-composite'] +
            magick_args[2] + [outimg])
    finally:
        os.remove(calimg)

def parse_range(s,hint=None):
    if '/' in s:
        t = s.split('/')
        month,span = parse_month_range(t[0])
        if hint and span == 0: span = hint
        year = parse_year(t[1])
        margs = []
        for m in xrange(span):
            margs += [(month,year)]
            month += 1
            if month > 12: month = 1; year += 1
        return margs
    else:
        raise Abort("calmagick: invalid range format '%s'" % options.range)

def range_worker(q,ev,i,verbose):
    while True:
        if ev.is_set():
            q.get()
            q.task_done()
        else:
            item = q.get()
#            if verbose: print "Thead-%d" % i
            try:
                compose_calendar(*item)
            except Exception as e:
                print >> sys.stderr, "Exception in Thread-%d: %s" % (i,e.args)
                ev.set()
            finally:
                q.task_done()

def main_program():
    parser = get_parser()

    magick_args = parse_magick_args()
    sys.argv,argv2 = extract_parser_args(sys.argv,parser,2)
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
        if options.verbose: print "Composing %d photos..." % len(mrange)
        if options.sample is not None:
            flist = random.sample(flist, options.sample if options.sample else len(mrange))
        nf = len(flist)
        if nf > 0:
            if options.jobs > 1:
                q = Queue.Queue()
                ev = threading.Event()
                for i in range(options.jobs):
                     t = threading.Thread(target=range_worker,args=(q,ev,i,options.verbose))
                     t.daemon = True
                     t.start()

            for i in range(len(mrange)):
                img = flist[i % nf]
                m,y = mrange[i]
                prefix = '' if options.prefix == 'no' else '%04d-%02d_' % (y,m)
                outimg = get_outfile(img,options.outdir,prefix,options.format)
                if options.jobs > 1:
                    q.put((img, outimg, options, [str(m), str(y)] + argv2, magick_args, (i+1,len(mrange))))
                else:
                    compose_calendar(img, outimg, options, [str(m), str(y)] + argv2, magick_args, (i+1,len(mrange)))

            if options.jobs > 1: q.join()
    else:
        img = args[0]
        if not os.path.isfile(img):
            raise Abort("calmagick: input image '%s' does not exist" % img)
        outimg = get_outfile(img,options.outdir,'',options.format,options.outfile)
        compose_calendar(img, outimg, options, argv2, magick_args)

if __name__ == '__main__':
    try:
        main_program()
    except Abort as e:
        sys.exit(e.args[0])
