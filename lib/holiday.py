# -*- coding: utf-8 -*-

#    callirhoe - high quality calendar rendering
#    Copyright (C) 2012-2013 George M. Tzoumas

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
"""       holiday support routines       """
#                                         #
# *****************************************

from datetime import date, timedelta

def _get_orthodox_easter(year):
    """compute date of orthodox easter
    @rtype: datetime.date
    """
    y1, y2, y3 = year % 4 , year % 7, year % 19
    a = 19*y3 + 15
    y4 = a % 30
    b = 2*y1 + 4*y2 + 6*(y4 + 1)
    y5 = b % 7
    r = 1 + 3 + y4 + y5
    return date(year, 3, 31) + timedelta(r)
#    res = date(year, 5, r - 30) if r > 30 else date(year, 4, r)
#    return res

def _get_catholic_easter(year):
    """compute date of catholic easter

    @rtype: datetime.date
    """
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b,4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i, k = divmod(c,4)
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    emonth,edate = divmod(h + l - 7*m + 114,31)
    return date(year, emonth, edate+1)

def _strip_empty(sl):
    """strip empty strings from list I{sl}

    @rtype: [str,...]
    """
    return filter(lambda z: z, sl) if sl else []

def _flatten(sl):
    """join list I{sl} into a comma-separated string

    @rtype: str
    """
    if not sl: return None
    return ', '.join(sl)

class Holiday(object):
    """class holding a Holiday object (date is I{not} stored, use L{HolidayProvider} for that)

    @ivar header_list: string list for header (primary text)
    @ivar footer_list: string list for footer (secondary text)
    @ivar flags: bit combination of {OFF=1, MULTI=2, REMINDER=4}

            I{OFF}: day off (real holiday)

            I{MULTI}: multi-day event (used to mark long day ranges,
            not necessarily holidays)

            I{REMINDER}: do not mark the day as holiday

    @note: Rendering style is determined considering L{flags} in this order:
                1. OFF
                2. MULTI

            First flag that matches determines the style.
    """
    OFF = 1
    MULTI = 2
    REMINDER = 4
    def __init__(self, header = [], footer = [], flags_str = None):
        self.header_list = _strip_empty(header)
        self.footer_list = _strip_empty(footer)
        self.flags = self._parse_flags(flags_str)

    def merge_with(self, hol_list):
        """merge a list of holiday objects into this object"""
        for hol in hol_list:
            self.header_list.extend(hol.header_list)
            self.footer_list.extend(hol.footer_list)
            self.flags |= hol.flags

    def header(self):
        """return a comma-separated string for L{header_list}

        @rtype: str
        """
        return _flatten(self.header_list)

    def footer(self):
        """return a comma-separated string for L{footer_list}

        @rtype: str
        """
        return _flatten(self.footer_list)

    def __str__(self):
        """string representation for debugging purposes

        @rtype: str
        """
        return str(self.footer()) + ':' + str(self.header()) + ':' + str(self.flags)

    def _parse_flags(self, fstr):
        """return a bit combination of flags, from a comma-separated string list

        @rtype: int
        """
        if not fstr: return 0
        fs = fstr.split(',')
        val = 0
        for s in fs:
            if s == 'off': val |= Holiday.OFF
            elif s == 'multi': val |= Holiday.MULTI
            # allow for prefix abbrev.
            elif 'reminder'.startswith(s): val |= Holiday.REMINDER
        return val

def _decode_date_str(ddef):
    """decode a date definition string into a I{(year,month,day)} tuple

    @param ddef: date definition string of length 2, 4 or 8

        If C{ddef} is of the form "DD" then tuple (0,0,DD) is returned, which
        stands for any year - any month - day DD.

        If C{ddef} is of the form "MMDD" then tuple (0,MM,DD) is returned, which
        stands for any year - month MM - day DD.

        If C{ddef} is of the form "YYYYMMDD" then tuple (YYYY,MM,DD) is returned, which
        stands for year YYYY - month MM - day DD.

    @rtype: (int,int,int)
    """
    if len(ddef) == 2:
        return (0,0,int(ddef))
    if len(ddef) == 4:
        return (0,int(ddef[:2]),int(ddef[-2:]))
    if len(ddef) == 8:
        return (int(ddef[:4]),int(ddef[4:6]),int(ddef[-2:]))
    raise ValueError("invalid date definition '%s'" % ddef)

class HolidayProvider(object):
    """class holding the holidays throught the year(s)

    @ivar annual: dict of events occuring annually, indexed by tuple I{(day,month)}. Note
    each dict entry is actually a list of L{Holiday} objects. This is also true for the other
    instance variables: L{monthly}, L{fixed}, L{orth_easter}, L{george}, L{cath_easter}.
    @ivar monthly: event occuring monthly, indexed by int I{day}
    @ivar fixed: fixed date events, indexed by a C{date()} object
    @ivar orth_easter: dict of events relative to the orthodox easter Sunday, indexed by
    an integer days offset
    @ivar george: events occuring on St George's day (orthodox calendar special computation)
    @ivar cath_easter: dict of events relative to the catholic easter Sunday, indexed by
    an integer days offset
    @ivar cache: for each year requested, all holidays occuring
    within that year (annual, monthly, easter-based etc.) are precomputed and stored into
    dict C{cache}, indexed by a C{date()} object
    @ivar ycache: set holding cached years; each new year requested, triggers a cache-fill
    operation
    """
    def __init__(self, s_normal, s_weekend, s_holiday, s_weekend_holiday, s_multi, s_weekend_multi, multiday_markers=True):
        """initialize a C{HolidayProvider} object

        @param s_normal: style class object for normal (weekday) day cells
        @param s_weekend: style for weekend day cells
        @param s_holiday: style for holiday day cells
        @param s_weekend_holiday: style for holiday cells on weekends
        @param s_multi: style for multi-day holiday weekday cells
        @param s_weekend_multi: style for multi-day holiday weekend cells
        @param multiday_markers: if C{True}, then use end-of-multiday-holiday markers and range markers (with dots),
        otherwise only first day and first-day-of-month are marked
        """
        self.annual = dict() # key = (d,m)
        self.monthly = dict() # key = d
        self.fixed = dict() # key = date()
        self.orth_easter = dict() # key = daysdelta
        self.george = [] # key = n/a
        self.cath_easter = dict() # key = daysdelta
        self.cache = dict() # key = date()
        self.ycache = set() # key = year
        self.s_normal = s_normal
        self.s_weekend = s_weekend
        self.s_holiday = s_holiday
        self.s_weekend_holiday = s_weekend_holiday
        self.s_multi = s_multi
        self.s_weekend_multi = s_weekend_multi
        self.multiday_markers = multiday_markers

    def _parse_day_record(self, fields):
        """return tuple (etype,ddef,footer,header,flags)

           @rtype: (char,type(ddef),str,str,int)
           @note: I{ddef} is one of the following:
                - None
                - int
                - ((y,m,d),)
                - ((y,m,d),(y,m,d))
        """
        if len(fields) != 5:
            raise ValueError("Too many fields: " + str(fields))
        for i in range(len(fields)):
            if len(fields[i]) == 0: fields[i] = None
        if fields[0] == 'd':
            if fields[1]:
                if '*' in fields[1]:
                    if fields[0] != 'd':
                        raise ValueError("multi-day events not allowed with event type '%s'" % fields[0])
                    dstr,spanstr = fields[1].split('*')
                    if len(dstr) != 8:
                        raise ValueError("multi-day events allowed only with full date, not '%s'" % dstr)
                    span = int(spanstr)
                    y,m,d = _decode_date_str(dstr)
                    dt1 = date(y,m,d)
                    dt2 = dt1 + timedelta(span-1)
                    res = ((y,m,d),(dt2.year,dt2.month,dt2.day))
                elif '-' in fields[1]:
                    if fields[0] != 'd':
                        raise ValueError("multi-day events not allowed with event type '%s'" % fields[0])
                    dstr,dstr2 = fields[1].split('-')
                    if len(dstr) != 8:
                        raise ValueError("multi-day events allowed only with full date, not '%s'" % dstr)
                    y,m,d = _decode_date_str(dstr)
                    y2,m2,d2 = _decode_date_str(dstr2)
                    res = ((y,m,d),(y2,m2,d2))
                else:
                    y,m,d = _decode_date_str(fields[1])
                    if len(fields[1]) == 8:
                        res = ((y,m,d),(y,m,d))
                    else:
                        res = ((y,m,d),)
            else:
                res = None
        else:
            res = int(fields[1])
        return (fields[0],res,fields[2],fields[3],fields[4])

    def _multi_holiday_tuple(self, header, footer, flags):
        """returns a 4-tuple of L{Holiday} objects representing (beginning, end, first-day-of-month, rest)

        @param header: passed as C{[header]} of the generated L{Holiday} object
        @param footer: passed as C{[footer]} of the generated L{Holiday} object
        @param flags: C{flags} of the generated L{Holiday} object
        @rtype: (Holiday,Holiday,Holiday,Holiday)
        """
        if header:
            if self.multiday_markers:
              header_tuple = (header+'..', '..'+header, '..'+header+'..', None)
            else:
              header_tuple = (header, None, header, None)
        else:
            header_tuple = (None, None, None, None)
        if footer:
            if self.multiday_markers:
              footer_tuple = (footer+'..', '..'+footer, '..'+footer+'..', None)
            else:
              footer_tuple = (footer, None, footer, None)
        else:
            footer_tuple = (None, None, None, None)
        return tuple(map(lambda k: Holiday([header_tuple[k]], [footer_tuple[k]], flags),
                         range(4)))

    def load_holiday_file(self, filename):
        """load a holiday file into the C{HolidayProvider} object

        B{File Format:}
            - C{type|date*span|footer|header|flags}
            - C{type|date1-date2|footer|header|flags}
            - C{type|date|footer|header|flags}

        I{type:}
            - C{d}: event occurs annually fixed day/month; I{date}=MMDD
            - C{d}: event occurs monthly, fixed day; I{date}=DD
            - C{d}: fixed day/month/year combination (e.g. deadline, trip, etc.); I{date}=YYYYMMDD
            - C{oe}: Orthodox Easter-dependent holiday, annually; I{date}=integer offset in days
            - C{ge}: Georgios' name day, Orthodox Easter dependent holiday, annually; I{date} field is ignored
            - C{ce}: Catholic Easter holiday; I{date}=integer offset in days

        I{date*span} and range I{date1-date2} supported only for I{date}=YYYYMMDD (fixed) events

        I{flags:} comma-separated list of the following:
            1. off
            2. multi
            3. reminder (or any prefix of it)

        B{Example}::

            d|0101||New year's|off
            d|0501||Labour day|off
            ce|-2||Good Friday|
            ce|0||Easter|off
            ce|1||Easter Monday|off
            d|20130223-20130310|winter vacations (B)||multi

        @param filename: file to be loaded
        """
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line[0] == '#': continue
                fields = line.split('|')
                etype,ddef,footer,header,flags = self._parse_day_record(fields)
                hol = Holiday([header], [footer], flags)
                if etype == 'd':
                    if len(ddef) == 1:
                        y,m,d = ddef[0]
                        if m > 0:           # annual event
                            if (d,m) not in self.annual: self.annual[(d,m)] = []
                            self.annual[(d,m)].append(hol)
                        else:               # monthly event
                            if d not in self.monthly: self.monthly[d] = []
                            self.monthly[d].append(hol)
                    else:                   # fixed date event
                        dt1,dt2 = date(*ddef[0]),date(*ddef[1])
                        span = (dt2-dt1).days + 1
                        if span == 1:
                            if dt1 not in self.fixed: self.fixed[dt1] = []
                            self.fixed[dt1].append(hol)
                        else:
                            # properly annotate multi-day events
                            hols = self._multi_holiday_tuple(header, footer, flags)
                            dt = dt1
                            while dt <= dt2:
                                if dt not in self.fixed: self.fixed[dt] = []
                                if dt == dt1: hol = hols[0]
                                elif dt == dt2: hol = hols[1]
                                elif dt.day == 1: hol = hols[2]
                                else: hol = hols[3]
                                self.fixed[dt].append(hol)
                                dt += timedelta(1)

                elif etype == 'oe':
                    d = ddef
                    if d not in self.orth_easter: self.orth_easter[d] = []
                    self.orth_easter[d].append(hol)
                elif etype == 'ge':
                    self.george.append(hol)
                elif etype == 'ce':
                    d = ddef
                    if d not in self.cath_easter: self.cath_easter[d] = []
                    self.cath_easter[d].append(hol)

    def get_holiday(self, y, m, d):
        """return a L{Holiday} object for the specified date (y,m,d) or C{None} if no holiday is defined

        @rtype: Holiday
        @note: If year I{y} has not been requested before, the cache is updated first
        with all holidays that belong in I{y}, indexed by C{date()} objects.
        """
        if y not in self.ycache:
            # fill-in events for year y
            # annual
            for d0,m0 in self.annual:
                dt = date(y,m0,d0)
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.annual[(d0,m0)])
            # monthly
            for d0 in self.monthly:
              for m0 in range(1,13):
                dt = date(y,m0,d0)
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.monthly[m0])
            # fixed
            for dt in filter(lambda z: z.year == y, self.fixed):
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.fixed[dt])
            # orthodox easter
            edt = _get_orthodox_easter(y)
            for delta in self.orth_easter:
                dt = edt + timedelta(delta)
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.orth_easter[delta])
            # Georgios day
            if self.george:
                dt = date(y,4,23)
                if edt >= dt: dt = edt + timedelta(1)  # >= or > ??
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.george)
            # catholic easter
            edt = _get_catholic_easter(y)
            for delta in self.cath_easter:
                dt = edt + timedelta(delta)
                if not dt in self.cache: self.cache[dt] = Holiday()
                self.cache[dt].merge_with(self.cath_easter[delta])

            self.ycache.add(y)

        dt = date(y,m,d)
        return self.cache[dt] if dt in self.cache else None

    def get_style(self, flags, dow):
        """return appropriate style object, depending on I{flags} and I{dow}

        @rtype: Style
        @param flags: bit combination of holiday flags
        @param dow: day of week
        """
        if flags & Holiday.OFF:
            return self.s_weekend_holiday if dow >= 5 else self.s_holiday
        if flags & Holiday.MULTI:
            return self.s_weekend_multi if dow >= 5 else self.s_multi
        return self.s_weekend if dow >= 5 else self.s_normal

    def __call__(self, year, month, dom, dow):
        """returns (header,footer,day_style)

        @rtype: (str,str,Style)
        @param month: month (0-12)
        @param dom: day of month (1-31)
        @param dow: day of week (0-6)
        """
        hol = self.get_holiday(year,month,dom)
        if hol:
            return (hol.header(),hol.footer(),self.get_style(hol.flags,dow))
        else:
            return (None,None,self.get_style(0,dow))

if __name__ == '__main__':
    import sys
    hp = HolidayProvider('n', 'w', 'h', 'wh', 'm', 'wm')
    if len(sys.argv) < 3:
        raise SystemExit("Usage: %s YEAR holiday_file ..." % sys.argv[0]);
    y = int(sys.argv[1])
    for f in sys.argv[2:]:
        hp.load_holiday_file(f)
    if y == 0: y = date.today().year
    cur = date(y,1,1)
    d2 = date(y,12,31)
    while cur <= d2:
        y,m,d = cur.year, cur.month, cur.day
        hol = hp.get_holiday(y,m,d)
        if hol: print cur.strftime("%a %b %d %Y"),hol
        cur += timedelta(1)
