#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import os.path
import subprocess

# mode.layout.sample -> extra args
ExtraArgs = {
    'landscape.classic.1x1': ["--phantom-days"],
    'landscape.bars.1x12': ["--padding=0.5", "--no-shadow"],
    'portrait.bars.1x6': ["--padding=0.7", "--no-shadow"]
    # *: []
}

# mode.layout.style.sample -> geometry
Geometries = {
    'landscape.classic.rainbow_gfs.3x4': ["default", "sloppy"]
    # *: ["default"]
}

# layout -> style
Styles = {
    'classic': ["gfs", "bw_gfs", "rainbow_gfs"],
    'bars': ["gfs", "bw_gfs", "rainbow_gfs"],
    'sparse': ["bw_sparse_gfs"]
}

# mode.layout -> sample
Samples = {
    'landscape.classic': [(1,1, ", 12 pages"), (2,2, ", 3 pages"), (3,4, "")],
    'landscape.bars': [(1,12, "")],
    'landscape.sparse': [(1,4, ", 3 pages"), (1,6, ", 2 pages")],
    'portrait.classic': [(4,3, "")],
    'portrait.bars': [(1,6, ", 2 pages")],
    'portrait.sparse': [(1,3, ", 4 pages")]
}


def spit_subsection(ctx,mode,layout,subsection):
    ctx.f.write('<h2>%s</h2>\n' % subsection)
    msuff = 'R' if mode == 'landscape' else ""
    for style in Styles[layout]:
        for p in Samples[mode+'.'+layout]:
            mlss = "%s.%s.%s.%dx%d" % (mode,layout,style,p[0],p[1])
            geoms = Geometries.get(mlss, ["default"])
            for g in geoms:
                gsuff = ""
                gstr = ""
                if g == "sloppy":
                    gsuff = "S"
                    gstr = ", sloppy"
                basename = "%s.%d.%s.%s.%dx%d%s%s"  % (layout,ctx.year,ctx.lang,style,p[0],p[1],gsuff,msuff)
                ctx.f.write('<p>%s style, %sx%s%s%s</p>\n' % (style, p[0], p[1], p[2], gstr))
                ctx.f.write('<p><a href="%s.pdf"><img src="%s.png" /></a></p>\n' % (basename,basename))
                ctx(mode,layout,style,g,(p[0],p[1]),basename)
    ctx.f.write('\n')


def spit_section(ctx,section):
    ctx.f.write('<h1>%s</h1>\n\n' % (section))
    mode = section.lower()
    spit_subsection(ctx, mode, "classic", "Classic layout")
    spit_subsection(ctx, mode, "bars", "Bars layout")
    spit_subsection(ctx, mode, "sparse", "Sparse layout")
    ctx.f.write('\n')


def spit_header(ctx):
    ctx.f.write("""    <!DOCTYPE html>
    <html>
      <head>
        <meta charset='utf-8'>
        <meta http-equiv="X-UA-Compatible" content="chrome=1">
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <link href='https://fonts.googleapis.com/css?family=Architects+Daughter' rel='stylesheet' type='text/css'>
        <link rel="stylesheet" type="text/css" href="../../../stylesheets/stylesheet.css" media="screen">
        <link rel="stylesheet" type="text/css" href="../../../stylesheets/pygment_trac.css" media="screen">
        <link rel="stylesheet" type="text/css" href="../../../stylesheets/print.css" media="print">

        <!--[if lt IE 9]>
        <script src="//html5shiv.googlecode.com/svn/trunk/html5.js"></script>
        <![endif]-->

        <title>Callirhoe - Downloadable Calendars</title>
      </head>

      <body>
        <header>
          <div class="inner">
            <h1>Callirhoe</h1>
            <h2>Downloadable Calendars</h2>
            <a href="https://github.com/geotz/callirhoe" class="button"><small>View project on</small> GitHub</a>
          </div>
        </header>

        <div id="content-wrapper">
          <div class="inner clearfix">
            <section id="main-content">

""")


def spit_footer(ctx):
    ctx.f.write("""
    </section>

    <aside id="sidebar">
      <a href="../../../DownloadableCalendars.html" class="button">
        <small>back to Downloadable</small>
        Calendars
      </a>

      <a href="../../../index.html" class="button">
        <small>back to</small>
        Main Page
      </a>

      <p class="repo-owner"><a href="https://github.com/geotz/callirhoe"></a> maintained by <a href="https://github.com/geotz">geotz</a>.</p>

      <p>This page was generated by <a href="https://pages.github.com">GitHub Pages</a> using the Architect theme by <a href="https://twitter.com/jasonlong">Jason Long</a>.</p>
    </aside>
  </div>
</div>


</body>
</html>
""")


def spit_main(ctx):
    try:
        os.makedirs(ctx.dirname)
    except:
        pass
    ctx.f = open('%s/index.html' % ctx.dirname, 'w')
    spit_header(ctx)
    ctx.f.write("<p>Screenshot of the first pdf page is shown. Click on it to download the full pdf calendar.</p>\n\n")
    spit_section(ctx,"Landscape")
    spit_section(ctx,"Portrait")
    spit_footer(ctx)
    ctx.f.close()


class Context:
    def __init__(self, year,lang, name, mrange, variant=None):
        self.year = year
        self.lang = lang
        self.name = name
        self.mrange = mrange
        self.f = None
        if variant is not None:
            self.hsuffix = '.'+variant[0]
            tmp = []
            for h in variant[1]:
                tmp.extend(['-H', 'holidays/'+h])
            self.hlist = tmp
        else:
            self.hsuffix = ""
            self.hlist = []
        self.dirname = '%s.%d/%s%s' % (self.name,self.year,self.lang,self.hsuffix)

    def __call__(self, mode, layout, style, geom, RxC, basename):
        print 'Generating %s/%s ...' % (self.dirname,basename)
        pdffile = '%s/%s.pdf' % (self.dirname,basename)
        pngfile = '%s/%s.png' % (self.dirname,basename)
        mls = "%s.%s.%dx%d" % (mode,layout,RxC[0],RxC[1])
        extra_args = ExtraArgs.get(mls, [])
        if os.path.exists(pdffile):
            print 'Skipping existing', pdffile
        else:
            paper = 'a4w' if mode == 'landscape' else 'a4'
            p = subprocess.Popen(['callirhoe', '-t', layout, '-s', style, '-g', geom, '--paper='+paper, '-l', self.lang,
                    '--rows=%d' % RxC[0], '--cols=%d' % RxC[1]] + self.hlist + extra_args + [self.mrange, str(self.year), pdffile])
            p.wait()
        #if p.returncode != 0: raise RuntimeError("autogen: calendar creation failed")
        if os.path.exists(pngfile):
            print 'Skipping existing', pngfile
        else:
            print 'Converting to png ...'
            width = '480' if mode == 'landscape' else '320'
            p = subprocess.Popen(['convert', '%s/%s.pdf[0]' % (self.dirname, basename), '-scale', width, pngfile])
            #p.wait() # optional...


lang_list = ['EN', 'EL', 'FR', 'DE', 'TR'];

# holiday variants
Variants = {
    'EN': [None, ('hol', ['generic_holidays.EN.dat'])],
    'EL': [None, ('hol', ['greek_holidays.EL.dat']), ('hol_nam', ['greek_holidays.EL.dat', 'greek_namedays.EL.dat'])],
    'FR': [None, ('hol', ['french_holidays.FR.dat']), ('hol_zA', ['french_holidays.FR.dat', 'french_holidays_zone_A.FR.dat']),
           ('hol_zB', ['french_holidays.FR.dat', 'french_holidays_zone_B.FR.dat']),
           ('hol_zC', ['french_holidays.FR.dat', 'french_holidays_zone_C.FR.dat'])],
    'DE': [None],
    'TR': [None]
}

BaseYear = 2017

for lang in lang_list:
    for v in Variants[lang]:
        spit_main(Context(BaseYear, lang, 'Calendar', '1:12', v))
        spit_main(Context(BaseYear-1, lang, 'Academic', '9:12', v))
