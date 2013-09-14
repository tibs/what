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

class What(object):
    """Report on events over a range of time.
    """

    def __init__(self, today=None, start_date=None, end_date=None):
        """Set up the range of dates we are interested in, and define 'today'
        """
        if today is None:
            today = datetime.date.today()

        outer_colon_methods = {':every': self.colon_every,
                               ':first': self.colon_first,
                               ':second': self.colon_first,
                               ':third': self.colon_first,
                               ':fourth': self.colon_first,
                               ':fifth': self.colon_first,
                               ':last': self.colon_last,
                               ':lastbutone': self.colon_lastbutone,
                               ':easter': self.colon_easter,
                               ':weekend': self.colon_weekend,
                               ':weekday': self.colon_weekday,
                              }

        boundary_colon_methods = {':except': self.colon_except,
                                  ':until': self.colon_until,
                                  ':weekly': self.colon_weekly,
                                  ':fortnightly': self.colon_fortnightly,
                                  ':monthly': self.colon_monthly,
                                 }

    def colon_every(self, words):
        """Every <something>

        <something> can be:

            * <day-name> -- every <day-name> in each week
            * <date> -- every <date> in each month
        """
        pass

    def colon_first(self, words):
        """The first <something>

        <something> can be:

            * <day-name> -- the first day of that name in a month
        """
        pass

    def colon_second(self, words):
        """The second <something>

        <something> can be:

            * <day-name> -- the second day of that name in a month
        """
        pass

    def colon_third(self, words):
        """The third <something>

        <something> can be:

            * <day-name> -- the third day of that name in a month
        """
        pass

    def colon_fourth(self, words):
        """The fourth <something>

        <something> can be:

            * <day-name> -- the fourth day of that name in a month
        """
        pass

    def colon_fifth(self, words):
        """The fifth <something> (maybe this will be useful sometime)

        <something> can be:

            * <day-name> -- the fifth day of that name in a month
        """
        pass

    def colon_last(self, words):
        """The last <something>

        <something> can be:

            * <day-name> -- the last day of that name in a month
        """
        pass

    def colon_lastbutone(self, words):
        """The last but one (penultimate) <something>

        <something> can be:

            * <day-name> -- the last but one day of that name in a month
        """
        pass

    def colon_easter(self, words):
        """A date related to Easter

        <something> can be 'Fri', 'Sat', 'Sun', 'Mon'. Alternatively, it can be
        a positive or negative number, for days relative to Easter Sunday - thus
        colon_easter(-1) is the same a colon_easter('Sat')
        """
        pass

    def colon_weekday(self, words):
        """A weekday before/after a weekend

        <something> can be:

        * 'after' <year> <month-name> <day>
        * 'before' <year> <month-name> <day>

        If the specified day *is* a weekday ('Mon'..'Fri'), then it is used,
        otherwise the nearest weekday before or after the given date is used.
        """
        pass

    def colon_weekend(self, words):
        """A weekend before/after a weekday

        <something> can be:

        * 'after' <year> <month-name> <day>
        * 'before' <year> <month-name> <day>

        If the specified day *is* a weekend ('Sat' or 'Sun'), then it is used,
        otherwise the nearest weekend day before or after the given date is used.
        """
        pass

    def colon_except(self, words):
        """An exception condition.

        <something> is <year> <month-name> <day>, and signifies the a date on
        which a repetitive event should not actually happen.

        Applies to the preceding date line
        """
        pass

    def colon_until(self, words):
        """An ending condition.

        <something> is <year> <month-name> <day>, and signifies the last date
        for a repetitive event.

        Applies to the preceding date line
        """
        pass

    def colon_weekly(self, words):
        """Repeating weekly.

        'words' should be empty.

        Applies to the preceding date line
        """
        pass

    def colon_fortnightly(self, words):
        """Repeating fortnightly

        'words' should be empty.

        Applies to the preceding date line
        """
        pass

    def colon_monthly(self, words):
        """Repeating monthly

        'words' should be empty.

        Applies to the preceding date line
        """
        pass

    def yield_lines(self, lines):
        """Yield interesting lines.

        Returns lists of the form:

            lineno, [text, ...]

        Empty lines and comment lines are not returned. Indented lines have their
        indentation removed, and are returned as the '...'.

        For instance:

            >>> w = What()
            >>> lines = ['# A comment',
            ...          'Line 2',
            ...          'Line 3',
            ...          '  line 3 continued',
            ...          'Line 5',
            ...          '  ',
            ...          'Line 7  ',
            ...          '  line 7 continued  ',
            ...          '  even more line 7  ',
            ...         ]
            >>> for line in w.yield_lines(lines):
            ...     print(line)
            (2, ['Line 2'])
            (3, ['Line 3', 'line 3 continued'])
            (5, ['Line 5'])
            (7, ['Line 7', 'line 7 continued', 'even more line 7'])

        but:

            >>> bad_lines = [' not line 1']
            >>> for line in w.yield_lines(bad_lines):
            ...     print(line)
            Traceback (most recent call last):
            ...
            GiveUp: Line 1 is indented, but follows the start of file

            >>> bad_lines = ['Line 1',
            ...              '# a comment',
            ...              '  not line 1',
            ...             ]
            >>> for line in w.yield_lines(bad_lines):
            ...     print(line)
            Traceback (most recent call last):
            ...
            GiveUp: Line 3 is indented, but follows a comment

            >>> bad_lines = ['Line 1',
            ...              '',
            ...              '  not line 1',
            ...             ]
            >>> for line in w.yield_lines(bad_lines):
            ...     print(line)
            Traceback (most recent call last):
            ...
            GiveUp: Line 3 is indented, but follows an empty line
        """
        lineno = 0
        last_was = 'the start of file'
        this_start = 0
        this_lines = []
        for line in lines:
            lineno += 1

            # Carefully lose trailing (but not leading) whitespace
            text = line.rstrip()

            # Empty lines are ignored
            if not text:
                last_was = 'an empty line'
                if this_lines:
                    yield this_start, this_lines
                    this_lines = []
                continue

            # Figure out if it is indented or not
            rest = text.lstrip()
            indented = rest != text
            text = rest

            # Any line with a hash in the first column is a comment
            if text[0] == '#':
                last_was = 'a comment'
                if this_lines:
                    yield this_start, this_lines
                    this_lines = []
                continue

            if indented:
                if this_lines:
                    this_lines.append(text)
                    last_was = 'an indented line'
                else:
                    raise GiveUp('Line {} is indented, but follows {}'.format(
                        lineno, last_was))
            else:
                if this_lines:
                    yield this_start, this_lines
                this_start = lineno
                this_lines = [text]
                last_was = 'a date line'

        if this_lines:
            yield this_start, this_lines

    def report_lines(self, lines):
        r"""Report on the given lines.

        For instance:

            >>> w = What()
            >>> w.report_lines([r'# This is a comment',
            ...                r'1960* Feb 18 Thu, Tibs is \a, born in \y',
            ...                r'2013 Sep 13 Fri, something # This is not a comment',
            ...                r'2013 Sep 14, another something',
            ...                r'  which continues',
            ...                r':every Thu, Thomas singing lesson',
            ...               ])
            --> 1960-02-18 Thu yearly
            --> 2013-09-13 Fri once
            --> 2013-09-14 Sat once
            ... which continues
            ::: :every Thu

        but:

            >>> w.report_lines([r'Fred'])
            Traceback (most recent call last):
            ...
            GiveUp: Missing comma in line 1
            Unindented lines should be of the form <date>, <rest>
            1: 'Fred'

            >>> w.report_lines([r'Fred,'])
            Traceback (most recent call last):
            ...
            GiveUp: No text after comma in line 1
            Unindented lines should be of the form <date>, <rest>
            1: 'Fred,'

            >>> w.report_lines([r'Fred, Jim'])
            Traceback (most recent call last):
            ...
            GiveUp: Error in line 1
            Date must be <year>[*] <month-name> <day>
                      or <year>[*] <month-name> <day> <day-name>
            not 'Fred'
            1: 'Fred, Jim'
        """
        lineno = 0
        for first_lineno, this_lines in self.yield_lines(lines):

            first_line = this_lines[0]
            more_lines = this_lines[1:]

            # We always want <thing>, <rest>
            parts = first_line.split(',')
            date_part = parts[0]
            rest = ','.join(parts[1:])

            if not rest:
                if ',' not in first_line:
                    raise GiveUp('Missing comma in line {}\n'
                                 'Unindented lines should be of the form <date>, <rest>\n'
                                 '{}: {!r}'.format(first_lineno, first_lineno, first_line))
                else:
                    raise GiveUp('No text after comma in line {}\n'
                                 'Unindented lines should be of the form <date>, <rest>\n'
                                 '{}: {!r}'.format(first_lineno, first_lineno, first_line))

            # Check for a magic word
            words = date_part.split()
            if words[0][0] == ':':
                print('::: {}'.format(date_part))
                continue

            try:
                date, day_name, yearly = parse_date(date_part)
            except GiveUp as e:
                raise GiveUp('Error in line {}\n{}\n{}: {!r}'.format(first_lineno,
                    e, first_lineno, first_line))

            print('--> {} {} {}'.format(date.isoformat(), day_name,
                'yearly' if yearly else 'once'))

            for text in more_lines:
                print('... {}'.format(text))

    def report_file(self, filename, start=None, end=None):
        """Report on the information in the named file.
        """
        with open(filename) as fd:
            self.report_lines(fd)

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
        elif word == '-for':
            # Take a date and report as if today were that date
            # Format of date should be as in the file, <year> <month> <day>
            raise GiveUp('Not yet implemented')
        elif word == '-calendar':
            # Print a calendar, for the current month or the named month
            # Format of date should be <year> <month>
            raise GiveUp('Not yet implemented')
        elif word == '-from':
            # Report events starting with this date
            # Format of date should be as in the file, <year> <month> <day>
            raise GiveUp('Not yet implemented')
        elif word == '-to':
            # Report events ending with this date
            # Format of date should be as in the file, <year> <month> <day>
            raise GiveUp('Not yet implemented')
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
