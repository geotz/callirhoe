import time

_version = "0.4.3"
_copyright = """Copyright (C) 2012-2015 George M. Tzoumas
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law."""

class Abort(Exception):
    pass

def extract_parser_args(arglist, parser, pos = -1):
    """extract options belonging to I{parser} along with I{pos} positional arguments

    @param arglist: argument list to extract
    @param parser: parser object to be used for extracting
    @param pos: number of positional options to be extracted

    if I{pos}<0 then all positional arguments are extracted, otherwise,
    only I{pos} arguments are extracted. arglist[0] (usually sys.argv[0]) is also positional
    argument!

    @rtype: ([str,...],[str,...])
    @return: tuple (argv1,argv2) with extracted argument list and remaining argument list
    """
    argv = [[],[]]
    posc = 0
    push_value = None
    for x in arglist:
        if push_value:
            push_value.append(x)
            push_value = None
            continue
        # get option name (long options stop at '=')
        y = x[0:x.find('=')] if '=' in x else x
        if x[0] == '-':
            if parser.has_option(y):
                argv[0].append(x)
                if not x.startswith('--') and parser.get_option(y).takes_value():
                    push_value = argv[0]
            else:
                argv[1].append(x)
        else:
            if pos < 0:
                argv[0].append(x)
            else:
                argv[posc >= pos].append(x)
                posc += 1
    return tuple(argv)

def atoi(s, lower_bound=None, upper_bound=None, prefix=''):
    """convert string to integer, exiting on error (for cmdline parsing)

    @param lower_bound: perform additional check so that value >= I{lower_bound}
    @param upper_bound: perform additional check so that value <= I{upper_bound}
    @param prefix: output prefix for error reporting
    @rtype: int
    """
    try:
        k = int(s);
        if lower_bound is not None:
            if k < lower_bound:
                raise Abort(prefix + "value '" + s +"' out of range: should not be less than %d" % lower_bound)
        if upper_bound is not None:
            if k > upper_bound:
                raise Abort(prefix + "value '" + s +"' out of range: should not be greater than %d" % upper_bound)
    except ValueError as e:
        raise Abort(prefix + "invalid integer value '" + s +"'")
    return k

def _parse_month(mstr):
    """get a month value (0-12) from I{mstr}, exiting on error (for cmdline parsing)

    @rtype: int
    """
    m = atoi(mstr,lower_bound=0,upper_bound=12,prefix='month: ')
    if m == 0: m = time.localtime()[1]
    return m

def parse_month_range(s):
    """return (Month,Span) by parsing range I{Month}, I{Month1}-I{Month2} or I{Month}:I{Span}

    @rtype: (int,int)
    """
    if ':' in s:
        t = s.split(':')
        if len(t) != 2: raise Abort("invalid month range '" + s + "'")
        Month = _parse_month(t[0])
        MonthSpan = atoi(t[1],lower_bound=0,prefix='month span: ')
    elif '-' in s:
        t = s.split('-')
        if len(t) != 2: raise Abort("invalid month range '" + s + "'")
        Month = _parse_month(t[0])
        MonthSpan = atoi(t[1],lower_bound=Month+1,prefix='month range: ') - Month + 1
    else:
        Month = _parse_month(s)
        MonthSpan = 1
    return (Month,MonthSpan)

def parse_year(ystr):
    """get a year value (>=0) from I{ystr}, exiting on error (for cmdline parsing)

    @rtype: int
    """
    y = atoi(ystr,lower_bound=0,prefix='year: ')
    if y == 0: y = time.localtime()[0]
    return y

