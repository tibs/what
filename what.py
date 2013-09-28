#! /usr/bin/env python2

# We stay with Python 2 for maximum portability, but assume 2.7

"""A "what happens when" utility, vaguely inspired by "when"

Comments start with '#' and end at end-of-line.

Empty lines (lines containing only whitespace and/or comments) are ignored.

Date lines are formed as::

    <date>, <text>

where <date> may be:

    * <yyyy> <mon> <day>
    * <yyyy> <mon> <day> <nam>
    * <yyyy>* <mon> <day>
    * <yyyy>* <mon> <day> <nam>
    * :<word>

<yyyy> is a four digit year number (e.g., '2013'), <mon> is a three character
(English) month abbreviation (case ignored, e.g. 'Jan' or 'dec' or even 'dEC'),
<day> is the day of the month ('1' through '31') and <nam> is a three character
day name (again, case ignored, e.g., 'Mon' or 'fri'). Dates with a day name are
always checked for correctness.

If the year has an asterisk immediately following, then the date means "every
year on this date, starting with this particular date". This is most useful for
anniversaries (e.g., birthdays), and the special word ':age' (meaning age in
years) will be recognised in <text>, and replaced with the appropriate number
(NOT YET IMPLEMENTED).

:<word> may be one of:

    * :every <something>, which may be:

      * :every <nam> -- meaning every week on that day, ':every Mon'
      * :every <mon> <day> -- meaning every equivalent date, ':every Dec 25'.
        If the selected day is Feb 29, and that doesn't exist this year, then
        it will be ignored for this year.
      * :every day <day> -- every month on that date, ':every day 8'
        Note that this will not set an event in months which do not have that
        date.

    * :first <nam> -- the first day of that name in a month, ':first Mon'
    * :second <nam> -- the second day of that name in a month
    * :third <nam>
    * :fourth <nam>
    * :fifth <nam>
    * :last <nam> -- the last day of that name in a month
    * :lastbutone <nam> -- the penultimate day of that name in a month
    * :easter <nam> -- where <nam> is 'Fri', 'Sat', 'Sun' or 'Mon'. 'easter
      Fri' means the Friday of Easter in the current year.
      Possibly also (although maybe not in the initial version of this script)
      :easter <index>, where <index> is relative to Easter Sunday, so ':easter
      -1' would mean the same as ':easter Sat'.

    Also, it is possible to select a day before or after a particular event,
    using:

        :<day-specifier> before <year> <mon> <day> [<nam>]
        :<day-specifier> after <year> <mon> <day> [<nam>]

    where <day-specifier> is one of:

        * <day> -- i.e., Mon..Sun, case ignored
        * weekend -- meaning the "nearest" Sat or Sun in the given direction
        * weekday -- meaning the "nearest" Mon .. Fri in the given direction

    for instance::

        :Mon before 2013 dec 25
        :weekend after 2013 dec 25 wed

    Note that "nearest" doesn't include the day itself, so::

        :Wed nefore 2013 dec 25 wed

    means Wednesday 18th December 2013, not Wednesday 25th December

    Also:

        :weekend before 2013 sep 29 sun

    means Saturday 28th September, not Sunday 29th.

The case of <word> is ignored.

<text> is free text, and is left as-is, except that the words:

    * :age
    * :year

(and maybe other quantities) will be replaced with the appropriate value.
Again, the case of these is ignored.
(NOT YET IMPLEMENTED).

Continuation lines follow date lines, and are indented. The amount of
indentaton is not significant, and is not checked (although it looks nicer if
it matches). A continuation line must start with a colon-word. Future versions
of the script *may* allow multiple colon-words on the same line, but this
version does not. Colon-words modify the preceding date line, and the available
modifiers are:

    * :except <year> <mon> <day> [<dat>] -- the preceding event does not occur
      on this particular day.
    * :until <year> <mon> <day> [<dat>] -- the preceding event continues until
      this date. If this date does not exactly match the recurrence of the
      preceding event, then the last occurrence is the one before this date.
    * :weekly -- the preceding event occurs weekly, i.e., every week on the
      same day.
    * :fortnightly -- the preceding event occurs fortnightly, i.e., every
      other week on the same day.
    * :monthly -- the preceding event occurs monthly, i.e., every month on the
      same date.
    * :every <count> days -- the preceding event occurs every <count> days,
      starting on the original date. ':every 7 days' is thus the same as
      ':weekly'.

The case of colon-words is ignored.
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

ORDINAL = {1: 'first', 2:'second', 3:'third', 4:'fourth', 5:'fifth',
           -1:'last', -2:'lastbutone'}

timespan_re = re.compile(r'(\d|\d\d):(\d\d)\.\.(\d|\d\d):(\d\d)')

class GiveUp(Exception):
    pass

def validate_day_name(date, day_name):
    if DAYS[date.weekday()] != day_name.capitalize():
        raise GiveUp('{} {} {} is {}, not {}'.format(year, month_name,
            day, DAYS[date.weekday()], day_name))

def day_after_date(date, day_name, today_ok=False):
    """Given a day name, return the date of that day *after* 'date'.

        >>> sat = datetime.date(year=2013, month=9, day=28)
        >>> sat.isoweekday()
        6
        >>> day_after_date(sat, 'Sun')
        datetime.date(2013, 9, 29)
        >>> day_after_date(sat, 'Mon')
        datetime.date(2013, 10, 3)

    if 'today_ok', then:

        >>> day_after_date(sat, 'Sat', True)
        datetime.date(2013, 9, 28)

    otherwise, we really *do* mean the day of that name *after* this date:

        >>> day_after_date(sat, 'Sat')
        datetime.date(2013, 10, 1)
    """
    if today_ok and day_name == DAYS[date.weekday()]:
        return date
    day_index = DAYS.index(day_name)+1      # range 1..7
    offset = day_index - date.isoweekday()  # isoweekday() is also 1..7
    if offset <= 0:
        offset += 7
    delta = datetime.timedelta(days=abs(offset))
    return date + delta

def day_before_date(date, day_name, today_ok=False):
    """Given a day name, return the date of that day *before* 'date'.

        >>> sat = datetime.date(year=2013, month=9, day=28)
        >>> sat.isoweekday()
        6
        >>> day_before_date(sat, 'Sun')
        datetime.date(2013, 9, 22)
        >>> day_before_date(sat, 'Mon')
        datetime.date(2013, 9, 23)

    if 'today_ok', then:

        >>> day_before_date(sat, 'Sat', True)
        datetime.date(2013, 9, 28)

    otherwise, we really *do* mean the day of that name *after* this date:

        >>> day_before_date(sat, 'Sat')
        datetime.date(2013, 9, 21)
    """
    if today_ok and day_name == DAYS[date.weekday()]:
        return date
    day_index = DAYS.index(day_name)+1      # range 1..7
    offset = day_index - date.isoweekday()  # isoweekday() is also 1..7
    if offset >= 0:
        offset -= 7
    delta = datetime.timedelta(days=offset)
    return date + delta

def calc_easter(year):
    """Returns Easter as a date object.

    From http://code.activestate.com/recipes/576517-calculate-easter-western-given-a-year/

    An implementation of `Butcher's Algorithm`_ for determining the date of
    Easter for the Western church. Works for any date in the Gregorian calendar
    (1583 and onward).

    .. _`Butcher's Algorithm`: http://www.smart.net/~mmontes/nature1876.html
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return datetime.date(year, month, day)

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
        validate_day_name(date, day_name)
    else:
        day_name = DAYS[date.weekday()]

    return date, day_name, yearly

class Event(object):
    """A representation of an event.
    """

    def __init__(self, date, day_name=None):
        """Create a basic event.

        A basic event occurs just once, on the date given.
        """
        self.date = date
        self.text = None

        if self.day_name is None:
            pass
        else:
            validate_day_name(date, day_name)
            self.day_name = day_name

        self.repeat_period = None
        self.repeat_yearly = False
        self.repeat_until = None
        self.repeat_on_day_name = set()
        self.repeat_on_day = set()
        self.repeat_ordinal = set()
        self.not_on = set()

    def set_text(self, text):
        self.text = text

    def __str__(self):
        return '{:4d} {:3} {:2d} {:3s}, {}'.format(self.date.year,
                MONTH_NAME[self.date.month], self.date.day, self.day_name,
                self.text)

    def __repr__(self):
        parts = []
        if self.repeat_yearly:
            year = '{}*'.format(self.date.year)
        else:
            year = '{}'.format(self.date.year)
        parts.append('{} {} {} {}, {}'.format(year,
            MONTH_NAME[self.date.month], self.date.day, self.day_name,
            self.text))
        # ... and then some representation of each colon word...
        if self.repeat_period:
            parts.append('    :every {} days'.format(self.repeat_period))
        if self.repeat_on_day_name:
            for day_name in sorted(self.repeat_on_day_name):
                parts.append('    :every {}'.format(day_name))
        if self.repeat_on_day:
            for day in sorted(self.repeat_on_day):
                parts.append('    :every day {}'.format(day))
        if self.repeat_ordinal:
            for which, day_name in sorted(self.repeat_ordinal):
                parts.append('    :{} {}'.format(ORDINAL[which], day_name))
        if self.not_on:
            for date in sorted(self.not_on):
                parts.append('    :except {} {} {}'.format(date.year,
                    MONTH_NAME[date.month], date.day))
        if self.repeat_until:
            parts.append('    :until {} {} {}'.format(self.repeat_until.year,
                MONTH_NAME[self.repeat_until.month], self.repeat_until.day))
        return '\n'.join(parts)

    def set_repeat_every(self, period):
        """The event repeats once every 'period' days.
        """
        self.repeat_period = period

    def set_repeat_on_day_name(self, day_name):
        """The event repeats on the given day name.
        """
        self.repeat_on_day_name.add(day_name)

    def set_repeat_on_day_each_month(self, day):
        """The event repeats on the given day every month.
        """
        self.repeat_on_day.add(day)

    def set_repeat_yearly(self):
        """The event repeats on the same date every year.
        """
        self.repeat_yearly = True

    def set_repeat_until(self, date):
        """Repeat until the given date (or before it).
        """
        self.repeat_until = date

    def set_repeat_ordinal(self, day_name, which):
        """Repeat on a given 'which' day.

        If 'which' is 1, the first 'day_name' of the month, 2 the second,
        -1 the last-but-one, and so on.
        """
        self.repeat_ordinal.add(which, day_name)

    def set_except(self, date):
        """Do not repeat on a specific day.
        """
        # Should we check it is within any range we have implied?
        # Or only do that when we "get_dates()"?
        self.not_on.add(date)

    def get_dates(self, start, end):
        """Given a start and end date, return those on which we occur.

        Returns a list of tuples of the form (date, text). This will be
        the empty list if there are no occurrences in the given range.
        """
        # Maybe sanity check our conditions lazily, at this point...
        return []

def colon_what(colon_word, words):
    """A simple utility to re-join :<word> commands for error reporting.
    """
    if words:
        return '{} {}'.format(colon_word, ' '.join(words))
    else:
        return colon_word

class What(object):
    """Report on events over a range of time.
    """

    def __init__(self, today=None, start_date=None, end_date=None):
        """Set up the range of dates we are interested in, and define 'today'

        * 'today' is the date to regard as this day - the default is today.
        * 'start_date' is the date to start reporting on - it defaults to the
          day before 'today'
        * 'end_date' is the date to stop reporting on - it defaults to the
          four weeks after 'today'

        All three should be datetime.date instances.

        For instance:

            >>> w = What(today=datetime.date(2013, 9, 14))
            >>> w.today
            datetime.date(2013, 9, 14)
            >>> w.start_date
            datetime.date(2013, 9, 13)
            >>> w.end_date
            datetime.date(2013, 10, 12)

        but:

            >>> w = What(today=datetime.date(2013, 9, 14),
            ...          start_date=datetime.date(2013, 9, 15))
            Traceback (most recent call last):
            ...
            GiveUp: Start date 2013-09-15 is after "today" 2013-09-14

        and so on.
        """
        if today is None:
            today = datetime.date.today()

        if start_date is None:
            # Use "yesterday"
            start_date = datetime.date.fromordinal(today.toordinal() - 1)

        if end_date is None:
            # Add four weeks
            end_date = datetime.date.fromordinal(today.toordinal() + 4*7)

        if start_date > today:
            raise GiveUp('Start date {} is after "today" {}'.format(
                start_date.isoformat(), today.isoformat()))

        if end_date < today:
            raise GiveUp('End date {} is before "today" {}'.format(
                end_date.isoformat(), today.isoformat()))

        if start_date > end_date:
            raise GiveUp('Start date {} is after end date {}'.format(
                start_date.isoformat(), end_date.isoformat()))

        self.today = today
        self.start_date = start_date
        self.end_date = end_date

        self.colon_event_methods = {':every': self.colon_event_every,
                                    ':first': self.colon_event_first,
                                    ':second': self.colon_event_first,
                                    ':third': self.colon_event_first,
                                    ':fourth': self.colon_event_first,
                                    ':fifth': self.colon_event_first,
                                    ':last': self.colon_event_last,
                                    ':lastbutone': self.colon_event_lastbutone,
                                    ':easter': self.colon_event_easter,
                                    ':weekend': self.colon_event_weekmagic,
                                    ':weekday': self.colon_event_weekmagic,
                                    ':mon': self.colon_event_weekmagic,
                                    ':tue': self.colon_event_weekmagic,
                                    ':wed': self.colon_event_weekmagic,
                                    ':thu': self.colon_event_weekmagic,
                                    ':fri': self.colon_event_weekmagic,
                                    ':sat': self.colon_event_weekmagic,
                                    ':sun': self.colon_event_weekmagic,
                                   }

        self.colon_condition_methods = {':except': self.colon_condition_except,
                                        ':until': self.colon_condition_until,
                                        ':weekly': self.colon_condition_weekly,
                                        ':fortnightly': self.colon_condition_fortnightly,
                                        ':monthly': self.colon_condition_monthly,
                                        ':every': self.colon_condition_repeat,
                                       }

    def colon_event_every(self, colon_word, words):
        """Every <something>

        <something> can be:

            * <day-name> -- every <day-name> in each week, ":every Mon"
            * <month-name> <day> -- every equivalent date, ":every Dec 25"
            * day <day> -- every <date> in each month, ":every day 8"
        """
        today = datetime.date.today()
        if len(words) == 1:
            day_name = words[0].capitalize()
            if day_name not in DAYS:
                raise GiveUp('Expected a day name (Mon..Fri), not {}\n'
                             'in {!r}'.format(day_name, colon_what(colon_word, words)))
            date = day_after_date(today, day_name, True)
            event = Event(date)
            event.set_repeat_every(7)
        elif len(words) != 2:
            raise GiveUp('Expected one of:\n'
                         '  :every <day-name>\n'
                         '  :every <month-name> <day>\n'
                         '  :every day <day>\n'
                         'not {!r}'.format(colon_what(colon_word, words)))

        if words[0] == 'day':
            try:
                day = int(words[1])
            except ValueError:
                raise GiveUp('Expected:\n'
                             '  :every day <day>\n'
                             'not {!r}'.format(colon_what(colon_word, words)))

            # If the day is 29..31, it is possible it might not be in *this*
            # month. Luckily, if that's so, we know that next month is always
            # a month with 31 days...
            try:
                date = today.replace(day=day)
            except ValueError:
                date = today.replace(day=day, month=today.month+1)
            event = Event(date)
            event.set_repeat_monthly()

        elif words[0].capitalize() in MONTH_NUMBER:
            try:
                day = int(words[1])
            except ValueError:
                raise GiveUp('Expected:\n'
                             '  :every {} <day>\n'
                             'not {!r}'.format(words[0], colon_what(colon_word, words)))
            month = MONTH_NUMBER[words[0].capitalize()]
            # If they ask for Feb 29 in a year that doesn't have it, we'll
            # have to choose the year after...
            try:
                date = today.replace(day=day, month=month)
            except ValueError:
                date = datetime.date(day=day, month=month, year=today.year+1)
            event = Event(date)
            event.repeat_yearly()

        else:
            raise GiveUp('Expected one of:\n'
                         '  :every <day-name>\n'
                         '  :every <month-name> <day>\n'
                         '  :every day <day>\n'
                         'not {!r}'.format(colon_what(colon_word, words)))
        return event

    def colon_event_first(self, colon_word, words):
        """The first <something>

        <something> can be:

            * <day-name> -- the first day of that name in a month, ":first Mon"
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_second(self, colon_word, words):
        """The second <something>

        <something> can be:

            * <day-name> -- the second day of that name in a month
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_third(self, colon_word, words):
        """The third <something>

        <something> can be:

            * <day-name> -- the third day of that name in a month
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_fourth(self, colon_word, words):
        """The fourth <something>

        <something> can be:

            * <day-name> -- the fourth day of that name in a month
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_fifth(self, colon_word, words):
        """The fifth <something> (maybe this will be useful sometime)

        <something> can be:

            * <day-name> -- the fifth day of that name in a month
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_last(self, colon_word, words):
        """The last <something>

        <something> can be:

            * <day-name> -- the last day of that name in a month, "last Mon"
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_lastbutone(self, colon_word, words):
        """The last but one (penultimate) <something>

        <something> can be:

            * <day-name> -- the last but one day of that name in a month
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_easter(self, colon_word, words):
        """A date related to Easter

        <something> can be 'Fri', 'Sat', 'Sun', 'Mon'. Alternatively, it can be
        a positive or negative number, for days relative to Easter Sunday - thus
        colon_event_easter(-1) is the same a colon_event_easter('Sat')

        For instance, ":easter Fri" or ":easter -10"
        """
        if len(words) != 1:
            raise GiveUp('Expected one of:\n'
                         '  :easter Fri|Sat|Sun|Mon\n'
                         '  :easter <offset>\n'
                         'not {!r}'.format(colon_what(colon_word, words)))
        when = words[0].capitalize()
        if when == 'Fri':
            offset = -2
        elif when == 'Sat':
            offset = -1
        elif when == 'Sun':
            offset = 0
        elif when == 'Mon':
            offset = 1
        else:
            try:
                offset = int(when)
            except ValueError as e:
                raise GiveUp('Expected one of:\n'
                             '  :easter Fri|Sat|Sun|Mon\n'
                             '  :easter <offset>\n'
                             'not {!r}\n'
                             'Error reading <offset>, {}'.format(colon_what(colon_word, words), e))

        today = datetime.date.today()
        easter = calc_easter(today.year)
        print(easter)
        date = easter + datetime.timedelta(days=offset)
        print(date)

        distance = today - easter
        distance = distance.days
        print(distance)

        # Let's try to get an Easter more-or-less in the future...
        if distance > 30:
            # Easter was a month ago...
            easter = calc_easter(today.year + 1)
            print(easter)
            date = easter + datetime.timedelta(days=offset)
            print(date)

        #raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_weekday(self, colon_word, words):
        """A weekday before/after a weekend

        <something> can be:

        * 'after' <year> <month-name> <day>
        * 'before' <year> <month-name> <day>

        If the specified day *is* a weekday ('Mon'..'Fri'), then it is used,
        otherwise the nearest weekday before or after the given date is used.
        """
        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_event_weekmagic(self, colon_word, words):
        """A day relative to a date

        * <something> 'after' <year> <month-name> <day> [<day-name>]
        * <something> 'before' <year> <month-name> <day> [<day-name>]

        where <something> is a day name, or 'weekday', or 'weekend'
        """
        try:
            day_name = words[0]
            when = words[1]
            date = ' '.join(words[2:])
        except IndexError:
                raise GiveUp('Expected one of:\n'
                             '  :<something> before <year> <mon> <day> [<nam>]\n'
                             '  :<something> after <year> <mon> <day> [<nam>]\n'
                             'not {!r}'.format(colon_what(colon_word, words)))

        raise GiveUp('NOT YET IMPLEMENTED')

    def colon_condition_except(self, colon_word, event, words):
        """An exception condition.

        <something> is <year> <month-name> <day>, and signifies the a date on
        which a repetitive event should not actually happen.

        Applies to the preceding date line
        """
        pass

    def colon_condition_until(self, colon_word, event, words):
        """An ending condition.

        <something> is <year> <month-name> <day>, and signifies the last date
        for a repetitive event. If the date does not exactly match the
        recurring event's date, then the last event is the one before this
        date.

        Applies to the preceding date line
        """
        pass

    def colon_condition_weekly(self, colon_word, event, words):
        """Repeating weekly.

        'words' should be empty.

        Applies to the preceding date line
        """
        pass

    def colon_condition_fortnightly(self, colon_word, event, words):
        """Repeating fortnightly

        'words' should be empty.

        Applies to the preceding date line
        """
        pass

    def colon_condition_monthly(self, colon_word, event, words):
        """Repeating monthly

        'words' should be empty.

        Applies to the preceding date line
        """
        # Which is just the same as repeating on the same day each month
        event.set_repeat_on_day_each_month(self.date.day)

    def colon_condition_repeat(self, colon_word, event, words):
        """Repeat every <something> days

        As in ":every 5 days"

        ":every 7 days" is thus the same as ":weekly"
        """
        if len(words) != 2 or words[1] != 'days':
            raise GiveUp("Expected ':repeat <num> days'\n"
                         'not {!r}'.format(colon_what(colon_word, words)))

        try:
            every = int(words[0])
        except ValueError:
            raise GiveUp('Expected:\n'
                         '  :every <every> days\n'
                         'not {!r}'.format(colon_what(colon_word, words)))
        event.set_repeat_every(every)

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
            ...                r'  :every 4 days',
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
                colon_word = words[0].lower()
                print('--> {}'.format(date_part))
                try:
                    fn = self.colon_event_methods[colon_word]
                    print('---  fn {}'.format(fn.__name__))
                    event = fn(colon_word, words[1:])
                    event.set_text(rest)
                except KeyError:
                    raise GiveUp('Error in line {}\n'
                                 'Unexpected ":" word as <date>, {!r}\n'
                                 '{}: {!r}'.format(lineno, colon_word, lineno, first_line))
                continue

            try:
                date, day_name, yearly = parse_date(date_part)
            except GiveUp as e:
                raise GiveUp('Error in line {}\n{}\n{}: {!r}'.format(first_lineno,
                    e, first_lineno, first_line))

            event = Event(date, day_name)
            event.set_text(rest)
            if yearly:
                event.set_repeat_yearly()

            print('--> {} {} {}'.format(date.isoformat(), day_name,
                'yearly' if yearly else 'once'))

            this_lineno = first_lineno
            for text in more_lines:
                this_lineno += 1
                print('... {}'.format(text))
                words = text.split()
                if words[0][0] == ':':
                    colon_word = words[0].lower()
                    try:
                        fn = self.colon_condition_methods[colon_word]
                        print('---  fn {}'.format(fn.__name__))
                        fn(colon_word, event, words[1:])
                    except KeyError:
                        raise GiveUp('Error in line {}\n'
                                     'Unexpected ":" word as <condition>, {!r}\n{}: {!r}'.format(
                                         this_lineno, colon_word, this_lineno, text))
                else:
                    raise GiveUp('Error in line {}\n'
                                 'Indented line should be a <condition>, starting with a colon,\n'
                                 '{}: {!r}'.format(this_lineno, this_lineno, text))

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
        w = What()
        w.report_file(filename)
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
