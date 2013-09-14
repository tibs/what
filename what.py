#! /usr/bin/env python2

# We stay with Python 2 for maximum portability, but assume 2.7

"""A "what happens when" utility, vaguely inspired by "when"
"""

from __future__ import division
from __future__ import print_function

import sys
import re
import datetime

MONTH_NUMBER = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}

MONTH_NAME = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
              7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

timespan_re = re.compile(r'(\d|\d\d):(\d\d)\.\.(\d|\d\d):(\d\d)')

class GiveUp(Exception):
    pass

def parse_date(text):
    """Given a text, turn it into a date.

    'text' should be either three words, of the form:

        <year>[*] <month-name> <day>

    of four words, of the form:

        <year>[*] <month-name> <day> <day-name>

    If the <year> is followed with '*', then it signifies an event that repeats
    yearly.

    If a <day-name> is given, it must agree with the date otherwise specified
    (and for a yearly event, with the original date)

    Returns a tuple of the form (datetime.date, day-name, yearly)

    For instance:

        >>> parse_date('2013 Sep 14')
        (datetime.date(2013, 9, 14), 'Sat', False)
        >>> parse_date('2013* Sep 14')
        (datetime.date(2013, 9, 14), 'Sat', True)
        >>> parse_date('2013 Sep 14 Sat')
        (datetime.date(2013, 9, 14), 'Sat', False)
        >>> parse_date('2013* Sep 14 Sat')
        (datetime.date(2013, 9, 14), 'Sat', True)

        >>> parse_date('Fred')
        Traceback (most recent call last):
        ...
        GiveUp: Date must be <year>[*] <month-name> <day>
                  or <year>[*] <month-name> <day> <day-name>
        not 'Fred'

    (that last aligns better if the "GiveUp: " is removed)

        >>> parse_date('Fred Sep 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Year 'Fred' is not an integer

        >>> parse_date('2013 Fred 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Month 'Fred' is not one of Jan..Feb

        >>> parse_date('2013 Sep Fred Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Day 'Fred' is not an integer

        >>> parse_date('2013 Sep 14 Fred')
        Traceback (most recent call last):
        ...
        GiveUp: Day name 'Fred' is not one of Mon..Sun

        >>> parse_date('2013 Sep 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: 2013 Sep 14 is Sat, not Fri

        >>> parse_date('2013 Sep 97')
        Traceback (most recent call last):
        ...
        GiveUp: Date '2013 Sep 97' is not a valid date: day is out of range for month
    """
    words = text.split()
    yearly = False
    if len(words) == 3:
        year, month_name, day = words
        day_name = None
    elif len(words) == 4:
        year, month_name, day, day_name = words
    else:
        raise GiveUp('Date must be <year>[*] <month-name> <day>\n'
                     '          or <year>[*] <month-name> <day> <day-name>\n'
                     'not {!r}'.format(' '.join(words)))

    if year[-1] == '*':
        year = year[:-1]
        yearly = True
    try:
        year = int(year)
    except ValueError:
        raise GiveUp('Year {!r} is not an integer'.format(year))

    if month_name.capitalize() not in MONTH_NUMBER:
        raise GiveUp('Month {!r} is not one of Jan..Feb'.format(month_name))

    try:
        day = int(day)
    except ValueError:
        raise GiveUp('Day {!r} is not an integer'.format(day))

    if day_name and day_name.capitalize() not in DAYS:
        raise GiveUp('Day name {!r} is not one of Mon..Sun'.format(day_name))

    try:
        date = datetime.date(year, MONTH_NUMBER[month_name], day)
    except ValueError as e:
        raise GiveUp('Date {!r} is not a valid date: {}'.format(text, e))

    if day_name:
        if DAYS[date.weekday()] != day_name.capitalize():
            raise GiveUp('{} {} {} is {}, not {}'.format(year, month_name,
                day, DAYS[date.weekday()], day_name))
    else:
        day_name = DAYS[date.weekday()]

    return date, day_name, yearly

def report_lines(lines):
    r"""Report on the given lines.

    For instance:

        >>> report_lines([r'# This is a comment',
        ...               r'1960* Feb 18 Thu, Tibs is \a, born in \y',
        ...               r'2013 Sep 13 Fri, something # another comment',
        ...               r'2013 Sep 14, another something',
        ...               r'  which continues # this is a comment as well',
        ...              ])
        --> 1960-02-18 Thu yearly
        --> 2013-09-13 Fri once
        --> 2013-09-14 Sat once
        ... which continues

    and, at least temporarily:

        >>> report_lines([r'w=1, something',
        ...               r'e=2, something',
        ...              ])
        ??? w=1, something
        ??? e=2, something

    (this is deliberately not tested beyond that)

    but:

        >>> report_lines([r'Fred'])
        Traceback (most recent call last):
        ...
        GiveUp: Missing comma in line 1
        Unindented lines should be of the form <date>, <rest>
        1: 'Fred'

        >>> report_lines([r'Fred,'])
        Traceback (most recent call last):
        ...
        GiveUp: No text after comma in line 1
        Unindented lines should be of the form <date>, <rest>
        1: 'Fred,'

        >>> report_lines([r'Fred, Jim'])
        Traceback (most recent call last):
        ...
        GiveUp: Error in line 1
        Date must be <year>[*] <month-name> <day>
                  or <year>[*] <month-name> <day> <day-name>
        not 'Fred'
        1: 'Fred, Jim'
    """
    lineno = 0
    for line in lines:
        lineno += 1
        commentary = line.split('#')
        text = commentary[0]

        # Carefully lose trailing (but not leading) whitespace
        text = text.rstrip()

        if not text:
            continue

        # Figure out if it is indented or not
        rest = text.lstrip()
        indented = rest != text
        text = rest

        if not indented:
            # We always want <thing>, <rest>
            parts = text.split(',')
            date_part = parts[0]
            rest = ','.join(parts[1:])

            # For compatility with "when", we also, perhaps temorarily,
            # accept <letter>=<expression> - this doesn't go anywhere near
            # handling the actual syntax used, but does cope with that I've
            # got in my example calendar file
            if date_part[0] in ('e', 'm', 'w', 'y') and date_part[1] == '=':
                print('??? {}'.format(text))
                continue

            if not rest:
                if ',' not in text:
                    raise GiveUp('Missing comma in line {}\n'
                                 'Unindented lines should be of the form <date>, <rest>\n'
                                 '{}: {!r}'.format(lineno, lineno, text))
                else:
                    raise GiveUp('No text after comma in line {}\n'
                                 'Unindented lines should be of the form <date>, <rest>\n'
                                 '{}: {!r}'.format(lineno, lineno, text))

            try:
                date, day_name, yearly = parse_date(date_part)
            except GiveUp as e:
                raise GiveUp('Error in line {}\n{}\n{}: {!r}'.format(lineno,
                    e, lineno, text))

            print('--> {} {} {}'.format(date.isoformat(), day_name,
                'yearly' if yearly else 'once'))
        else:
            # Indented lines are continuations
            print('... {}'.format(text))

def report_file(filename, start=None, end=None):
    """Report on the information in the named file.
    """
    with open(filename) as fd:
        report_lines(fd)

def report(args):
    filename = None
    show_comments = False
    while args:
        word = args.pop(0)
        if word in ('-h', '-help', '--help', '/?', '/help'):
            print(__doc__)
            return
        elif word == '-doctest':
            import doctest
            failures, tests = doctest.testmod()
            if failures:
                raise GiveUp('The light is RED')
            else:
                print('The light is GREEN')
            return
        elif word[0] == '-' and not os.path.exists(word):
            raise GiveUp('Unexpected switch {:r}'.format(word))
        elif not filename:
            filename = word
        else:
            raise GiveUp('Unexpected argument {:r} (already got'
                         ' filename {:r}'.format(word. filename))

    if not filename:
        filename = 'calendar.txt'

    try:
        report_file(filename)
    except GiveUp as e:
        raise GiveUp('Error reading file {!r}\n{}'.format(filename, e))

if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        report(args)
    except GiveUp as e:
        print(e)
        sys.exit(1)

# vim: set tabstop=8 softtabstop=4 shiftwidth=4 expandtab:
