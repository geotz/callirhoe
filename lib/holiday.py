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
#       holiday support routines          #
#                                         #
# *****************************************

from datetime import date, timedelta

def _get_orthodox_easter(year):
    """compute date of orthodox easter"""
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
    """compute date of catholic easter"""
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

class Holiday(object):
    """class holding a Holiday object (date is not stored!)

    Properties:
        header: string for header
        footer: string for footer
        flags : bit combination of {OFF=1, MULTI=2}
            OFF: day off (real holiday)
            MULTI: multi-day event (used to mark long day ranges,
                                    not necessarily holidays)

    Remarks:
        Rendering style is considered in the following order:
            1) OFF
            2) MULTI
        First flag that matches determines the style
    """
    OFF = 1
    MULTI = 2
    def __init__(self, header = [], footer = [], flags_str = None):
        self.header_list = self._strip_empty(header)
        self.footer_list = self._strip_empty(footer)
        self.flags = self._parse_flags(flags_str)

    def merge_with(self, hol_list):
        for hol in hol_list:
            self.header_list.extend(hol.header_list)
            self.footer_list.extend(hol.footer_list)
            self.flags |= hol.flags

    def header(self):
        return self._flatten(self.header_list)

    def footer(self):
        return self._flatten(self.footer_list)

    def __repr__(self):
        return str(self.footer()) + ':' + str(self.header()) + ':' + str(self.flags)

    def _parse_flags(self, fstr):
        if not fstr: return 0
        fs = fstr.split(',')
        val = 0
        for s in fs:
            if s == 'off': val |= Holiday.OFF
            elif s == 'multi': val |= Holiday.MULTI
        return val

    def _strip_empty(self, sl):
        return filter(lambda z: z, sl) if sl else []

    def _flatten(self, sl):
        if not sl: return None
        res = sl[0]
        for s in sl[1:]:
            res += ', ' + s
        return res

class HolidayProvider(object):
    def __init__(self, s_normal, s_weekend, s_holiday, s_weekend_holiday, s_multi, s_weekend_multi):
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

    def parse_day_record(self, fields):
        """return tuple (etype,d,m,y,span,footer,header,flags)"""
        if len(fields) != 7:
            raise ValueError("Too many fields: " + str(fields))
        for i in range(len(fields)):
            if len(fields[i]) == 0: fields[i] = None
        if fields[1]:
            if '*' in fields[1]:
                if fields[0] != 'f':
                    raise ValueError("multi-day events not allowed with event type '%s'" % fields[0])
                d,span = map(int,fields[1].split('*'))
            else: d,span = int(fields[1]), 1
        else: d,span = 0,0
        m = int(fields[2]) if fields[2] else 0
        y = int(fields[3]) if fields[3] else 0
        return (fields[0],d,m,y,span,fields[4],fields[5],fields[6])

    def multi_holiday_tuple(self, date1, date2, header, footer, flags):
        """returns Holiday objects for (beginning, end, first_dom, rest)"""
        if header:
            header_tuple = (header+'..', '..'+header, '..'+header+'..', None)
        else:
            header_tuple = (None, None, None, None)
        if footer:
            footer_tuple = (footer+'..', '..'+footer, '..'+footer+'..', None)
        else:
            footer_tuple = (None, None, None, None)
        return tuple(map(lambda k: Holiday([header_tuple[k]], [footer_tuple[k]], flags),
                         range(4)))

    # File Format:
    # type|day*span|month|year|footer|header|off
    # type|day|month|year|footer|header|off
    # day*span supported only for f
    # Type:
    # a: holiday occurs annually fixed day/month
    # m: holiday occurs monthly, fixed day
    # f: fixed day/month/year combination (e.g. deadline, trip, etc.)
    # oe: Orthodox Easter-dependent holiday, annually
    # ge: Georgios' name day, Orthodox Easter dependent holiday, annually
    # ce: Catholic Easter holiday
    def load_holiday_file(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line[0] == '#': continue
                fields = line.split('|')
                etype,d,m,y,span,footer,header,flags = self.parse_day_record(fields)
                hol = Holiday([header], [footer], flags)
                if etype == 'a':
                    if (d,m) not in self.annual: self.annual[(d,m)] = []
                    self.annual[(d,m)].append(hol)
                elif etype == 'm':
                    if d not in self.monthly: self.monthly[d] = []
                    self.monthly[d].append(hol)
                elif etype == 'f':
                    if span == 1:
                        if date(y,m,d) not in self.fixed: self.fixed[date(y,m,d)] = []
                        self.fixed[date(y,m,d)].append(hol)
                    else:
                        # properly annotate multi-day events
                        dt1 = date(y,m,d)
                        dt2 = dt1 + timedelta(span-1)
                        hols = self.multi_holiday_tuple(dt1, dt2, header, footer, flags)
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
                    if d not in self.orth_easter: self.orth_easter[d] = []
                    self.orth_easter[d].append(hol)
                elif etype == 'ge':
                    self.george.append(hol)
                elif etype == 'ce':
                    if d not in self.cath_easter: self.cath_easter[d] = []
                    self.cath_easter[d].append(hol)

    def get_holiday(self, y, m, d):
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
        if flags & Holiday.OFF:
            return self.s_weekend_holiday if dow >= 5 else self.s_holiday
        if flags & Holiday.MULTI:
            return self.s_weekend_multi if dow >= 5 else self.s_multi
        return self.s_weekend if dow >= 5 else self.s_normal

    def __call__(self, year, month, dom, dow):
        """returns (header,footer,day_style)

        Args:
            month: month (0-12)
            dom: day of month (1-31)
            dow: day of week (0-6)
        """
        hol = self.get_holiday(year,month,dom)
        if hol:
            return (hol.header(),hol.footer(),self.get_style(hol.flags,dow))
        else:
            return (None,None,self.get_style(0,dow))

if __name__ == '__main__':
    import sys
    hp = HolidayProvider('n', 'w', 'h', 'wh', 'm', 'wm')
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
