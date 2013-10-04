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
    * :<date-word> <other-stuff>

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

:<date-word> <other-stuff> may be any of:

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
    * :easter <nam> <year> -- where <nam> is 'Fri', 'Sat', 'Sun' or 'Mon'
      ('easter Fri' means the Friday of Easter in that current year), or
    * :easter <index> <year>, where <index> is relative to Easter Sunday, so
      ':easter -1 2013' would mean the same as ':easter Sat 2013'.

    (Including the year on :easter makes it clearer what is intended - a
    mechanism for specifying "every easter" can be added later if needed,
    maybe just by allowing the year to be omitted.)

    Also, it is possible to select a day before or after a particular event,
    using:

        :<day-specifier> before <year> <mon> <day> [<nam>]
        :<day-specifier> after <year> <mon> <day> [<nam>]
        :<day-specifier> on-or-before <year> <mon> <day> [<nam>]
        :<day-specifier> on-or-after <year> <mon> <day> [<nam>]

    where <day-specifier> is one of:

        * <day> -- i.e., Mon..Sun, case ignored
        * weekend -- meaning the "nearest" Sat or Sun in the given direction
        * weekday -- meaning the "nearest" Mon .. Fri in the given direction

    for instance::

        :Mon before 2013 dec 25
        :weekend after 2013 dec 25 wed

    Note that "nearest" doesn't include the day itself, so::

        :Wed before 2013 dec 25 wed

    means Wednesday 18th December 2013, not Wednesday 25th December. If you
    want to allow the day itself, use on-or-before or on-or-after::

        :Wed on-or-before 2013 dec 25 wed

    is the 25th.

    Similarly:

        :weekend before 2013 sep 29 sun

    means Saturday 28th September, but:

        :weekend on-or-before 2013 sep 29 sun

    means Sunday 29th

The case of <word> is ignored.

<text> is free text, and is left as-is, except that the words:

    * :age
    * :year

(and maybe other quantities) will be replaced with the appropriate value.
Again, the case of these is ignored.
(NOT YET IMPLEMENTED).

<text> may also contain @<word> words, which will later on be usable to select
only events that contain particular values of @<word>.

Continuation lines follow date lines, and are indented. The amount of
indentaton is not significant, and is not checked (although it looks nicer if
it matches). A continuation line must start with a colon-word. Future versions
of the script *may* allow multiple colon-words on the same line, but this
version does not. Colon-words modify the preceding date line, and the available
modifiers are:

    * :except <year> <mon> <day> [<dat>][, <reason> -- the preceding event does
      not occur on this particular day. This is the only colon word to take
      a ", <text>" after its date, ALTHOUGH THAT MAY CHANGE IN FUTURE VERSIONS
      OF THE SCRIPT.
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
      ':weekly'. I apologise in advance for ':every 1 days'.
    * :for <count> days -- for that many days, including the original date
    * :for <count> weekdays -- for that many Mon..Fri days. Note that if the
      original date is a Sat or Sun, it/they won't count to the total. Works
      exactly as if it were a combination of ':for <n> days' with the internal
      weekend days excluded using ':except <weekend-day>'.

The case of colon-words is ignored.
"""

from __future__ import division
from __future__ import print_function

import calendar
import datetime
import os
import re
import subprocess
import sys

from functools import total_ordering

MONTH_NUMBER = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}

MONTH_NAME = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
              7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

ORDINAL = {1: 'first', 2:'second', 3:'third', 4:'fourth', 5:'fifth',
           -1:'last', -2:'lastbutone'}

timespan_re = re.compile(r'(\d|\d\d):(\d\d)\.\.(\d|\d\d):(\d\d)')

# Carefully match at either the start of the line/string or after a non-word,
# and then accept the @ or : character followed by alphanumerics of either case
at_word_re = re.compile(r'(?:^|\W)(@\w+)')
colon_word_re = re.compile(r'(?:^|\W)(:\w+)')

class GiveUp(Exception):
    pass

def validate_day_name(date, day_name):
    """Check that date has the given day name.

    Raise an exception if it does not.
    """
    if DAYS[date.weekday()] != day_name.capitalize():
        raise GiveUp('{} {} {} is {}, not {}'.format(date.year,
            MONTH_NAME[date.month], date.day,
            DAYS[date.weekday()], day_name))

def day_after_date(date, day_name, today_ok=False):
    """Given a day name, return the date of that day *after* 'date'.

        >>> sat = datetime.date(year=2013, month=9, day=28)
        >>> sat.isoweekday()
        6
        >>> day_after_date(sat, 'Sun')
        datetime.date(2013, 9, 29)
        >>> day_after_date(sat, 'Mon')
        datetime.date(2013, 9, 30)

    if 'today_ok', then:

        >>> day_after_date(sat, 'Sat', True)
        datetime.date(2013, 9, 28)

    otherwise, we really *do* mean the day of that name *after* this date:

        >>> day_after_date(sat, 'Sat')
        datetime.date(2013, 10, 5)
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

def calc_ordinal_day(start, ordinal, day_name):
    """Return the 'ordinal'th day called 'day_name' in 'start's month.

    Returns a date, or None (the latter should only really occur when
    the ordinal is 5). Currently, 'ordinal' may be -2, -1, 1, 2, 3, 4 or 5.

    For instance:

        >>> print(calc_ordinal_day(datetime.date(2013, 10, 2), 1, 'Wed'))
        2013-10-02
        >>> print(calc_ordinal_day(datetime.date(2013, 10, 2), 5, 'Thu'))
        2013-10-31
        >>> print(calc_ordinal_day(datetime.date(2013, 10, 2), 5, 'Fri'))
        None
    """

    if day_name not in DAYS:
        raise GiveUp('Ordinal day {!r} is not supported'.format(day_name))

    if ordinal == 1:
        first_day_of_month = start.replace(day=1)
        date = day_after_date(first_day_of_month, day_name, True)
    elif ordinal == 2:
        a_week_after_start = start.replace(day=1+7)
        date = day_after_date(a_week_after_start, day_name, True)
    elif ordinal == 3:
        two_weeks_after_start = start.replace(day=1+7+7)
        date = day_after_date(two_weeks_after_start, day_name, True)
    elif ordinal == 4:
        three_weeks_after_start = start.replace(day=1+7+7+7)
        date = day_after_date(three_weeks_after_start, day_name, True)
    elif ordinal == 5:
        four_weeks_after_start = start.replace(day=1+7+7+7+7)
        date = day_after_date(four_weeks_after_start, day_name, True)
        if date.month != start.month:
            return None
    elif ordinal == -1:
        last_day_of_month = start.replace(day=month_len)
        date = day_before_date(last_day_of_month, day_name, True)
    elif ordinal == -2:
        first_weekday, month_len = calendar.monthrange(start.year, start.month)
        a_week_before_end = start.replace(day=month_len-7)
    else:
        raise GiveUp('Ordinal index {} is not supported'.format(ordinal))
    return date

def parse_year_month_day(text):
    """Given a text containing an actual date, turn it into a datetime date.

    'text' should be either three words, of the form:

        <year>[*] <month-name> <day>

    or four words, of the form:

        <year>[*] <month-name> <day> <day-name>

    If the <year> is followed with '*', then it signifies an event that repeats
    yearly.

    If a <day-name> is given, it must agree with the date otherwise specified
    (and for a yearly event, with the original date)

    Returns a tuple of the form (datetime.date, yearly)

    For instance:

        >>> parse_year_month_day('2013 Sep 14')
        (datetime.date(2013, 9, 14), False)
        >>> parse_year_month_day('2013* Sep 14')
        (datetime.date(2013, 9, 14), True)
        >>> parse_year_month_day('2013 Sep 14 Sat')
        (datetime.date(2013, 9, 14), False)
        >>> parse_year_month_day('2013* Sep 14 Sat')
        (datetime.date(2013, 9, 14), True)

        >>> parse_year_month_day('Fred')
        Traceback (most recent call last):
        ...
        GiveUp: Date must be <year>[*] <month-name> <day>
                  or <year>[*] <month-name> <day> <day-name>
        not 'Fred'

    (that last aligns better if the "GiveUp: " is removed)

        >>> parse_year_month_day('Fred Sep 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Year 'Fred' is not an integer

        >>> parse_year_month_day('2013 Fred 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Month 'Fred' is not one of Jan..Feb

        >>> parse_year_month_day('2013 Sep Fred Fri')
        Traceback (most recent call last):
        ...
        GiveUp: Day 'Fred' is not an integer

        >>> parse_year_month_day('2013 Sep 14 Fred')
        Traceback (most recent call last):
        ...
        GiveUp: Day name 'Fred' is not one of Mon..Sun

        >>> parse_year_month_day('2013 Sep 14 Fri')
        Traceback (most recent call last):
        ...
        GiveUp: 2013 Sep 14 is Sat, not Fri

        >>> parse_year_month_day('2013 Sep 97')
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

    return date, yearly

@total_ordering
class Event(object):
    """A representation of an event.
    """

    def __init__(self, date):
        self.date = date
        self._text = None

        # If this event was actually specified with a colon date (e.g.,
        # :easter), then we can remember it, for later reporting back
        self.colon_date = None

        # Repeat on this same date every year. Silently do nothing if the date
        # (obviously, 29th February) doesn't occur in a year.
        self.repeat_yearly = False

        # Repeat every N days, for each N
        self.repeat_every_N_days = set()

        # Repeat on the Nth day of the month, for each N
        self.repeat_on_Nth_of_month = set()

        # Stop repeating on the given date. If that date is a day we would
        # repeat on, then keep it.
        self.repeat_until = None

        # Repeat on a given 'which'th day
        # Takes a tuple of the form (ordinal, day-name), so (1, 'Tue') means
        # the first Tuesday of the month, and (-1, 'Wed') means the last
        # Wednesday of the month
        self.repeat_ordinal = set()

        # Do not occur on the specified dates. We don't particularly care
        # if a date is a date we wouldn't have occurred on anyway...
        # Stored as tuples of the form (<date>, <reason-text>) or
        # (<date>, '') if there was no reason given
        self.not_on = set()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        """Set the text field of an event.

        Also finds any <at-word> or <colon-word> occurrences therein:

            >>> e = Event(datetime.date(2012, 10, 3))
            >>> e.text = 'Fred'
            >>> e.text
            'Fred'
            >>> print(e.at_words)
            set([])
            >>> print(e.colon_words)
            set([])
            >>> e.text = '@Jim,Fred :age,:year, @jim/@bob'
            >>> e.text
            '@Jim,Fred :age,:year, @jim/@bob'
            >>> sorted(e.at_words)
            ['@bob', '@jim']
            >>> sorted(e.colon_words)
            [':age', ':year']
        """
        self._text = value

        # Is there anything interesting in the text...
        self.at_words = set([x.lower() for x in re.findall(at_word_re, value)])
        self.colon_words = set([x.lower() for x in re.findall(colon_word_re, value)])

    @property
    def day_name(self):
        return DAYS[self.date.weekday()]

    def __str__(self):
        """Return something meant to be close to what the user wrote.
        """
        parts = []

        if self.colon_date:
            parts.append('{}, {}'.format(self.colon_date, self._text))
        else:
            parts.append('{} {} {:2d} {}, {}'.format(self.date.year,
                MONTH_NAME[self.date.month], self.date.day, self.day_name,
                self._text))

        # We have to guess whether the user had a star after the year,
        # or wrote ':yearly'. Go with the latter, in case I stop supporting
        # the former
        if self.repeat_yearly:
            parts.append('  :yearly')

        if self.repeat_every_N_days:
            for n in sorted(self.repeat_every_N_days):
                if n == 7:
                    # We don't remember which way the user specified it,
                    # so we'll choose the "friendlier"
                    parts.append('  :every {}'.format(self.day_name))
                else:
                    parts.append('  :every {} days'.format(n))

        if self.repeat_on_Nth_of_month:
            for n in sorted(self.repeat_on_Nth_of_month):
                parts.append('  :every {} day'.format(n))

        if self.repeat_ordinal:
            for index, day_name in sorted(self.repeat_ordinal):
                parts.append('  :{} {}'.format(ORDINAL[index], day_name))

        if self.repeat_until:
            parts.append('  :until {} {} {}'.format(self.repeat_until.year,
                MONTH_NAME[self.repeat_until.month], self.repeat_until.day))

        if self.not_on:
            for date, reason in sorted(self.not_on):
                if reason:
                    parts.append('  :except {} {} {} {}, {}'.format(date.year,
                        MONTH_NAME[date.month], date.day, DAYS[date.weekday()],
                        reason))
                else:
                    parts.append('  :except {} {} {} {}'.format(date.year,
                        MONTH_NAME[date.month], date.day, DAYS[date.weekday()]))

        return '\n'.join(parts)

    def __repr__(self):
        """Return something showing how we interpreted what the user wrote.

        Which mainly means a specific date, even if they used a colon date.
        """
        parts = []
        parts.append('{} {} {:2d} {}, {}'.format(self.date.year,
            MONTH_NAME[self.date.month], self.date.day, self.day_name,
            self._text))

        if self.repeat_yearly:
            parts.append('  :yearly')

        if self.repeat_every_N_days:
            for n in sorted(self.repeat_every_N_days):
                if n == 7:
                    # We don't remember which way the user specified it,
                    # so we'll choose the "friendlier"
                    parts.append('  :every {}'.format(self.day_name))
                else:
                    parts.append('  :every {} days'.format(n))

        if self.repeat_on_Nth_of_month:
            for n in sorted(self.repeat_on_Nth_of_month):
                parts.append('  :every {} day'.format(n))

        if self.repeat_ordinal:
            for index, day_name in sorted(self.repeat_ordinal):
                parts.append('  :{} {}'.format(ORDINAL[index], day_name))

        if self.repeat_until:
            parts.append('  :until {} {} {}'.format(self.repeat_until.year,
                MONTH_NAME[self.repeat_until.month], self.repeat_until.day))

        if self.not_on:
            for date, reason in sorted(self.not_on):
                if reason:
                    parts.append('  :except {} {} {} {}, {}'.format(date.year,
                        MONTH_NAME[date.month], date.day, DAYS[date.weekday()],
                        reason))
                else:
                    parts.append('  :except {} {} {} {}'.format(date.year,
                        MONTH_NAME[date.month], date.day, DAYS[date.weekday()]))

        if self.at_words:
            parts.append('  <at-words> {}'.format(', '.join(sorted(self.at_words))))

        if self.colon_words:
            parts.append('  <colon-words> {}'.format(', '.join(sorted(self.colon_words))))

        return '\n'.join(parts)

    def __hash__(self):
        """A terribly simple and quite inefficient hash of ourselves.
        """
        parts = str(self).split('\n')
        return hash(' '.join(parts))

    def __eq__(self, other):
        if self.date != other.date:
            return False
        # Otherwise, revert to a big stick
        return str(self) == str(other)

    def __lt__(self, other):
        if self.date < other.date:
            return True
        elif self.date > other.date:
            return False
        else:
            # Anything after that is somewhat arbitrary - do I even care?
            if str(self) < str(other):
                return True
            else:
                return False

    def get_dates(self, start, end, at_words=None):
        """Given a start and end date, return those on which we occur.

        Returns a list of tuples of the form (date, text, event). This will be
        the empty list if there are no occurrences in the given range. Note
        that we need to include the text because it may have been altered from
        the event.text
        """
        # Maybe sanity check our conditions lazily, at this point...
        # ...or maybe not

        # If the caller asked for only texts that have particular at-words
        # within them, then we should/can check that first
        if at_words and not at_words.intersection(self.at_words):
            # OK, we don't match
            return []

        dates = set()

        if self.repeat_until:
            if self.repeat_until < start:
                #print(self)
                #print('repeat until {} is before start {}'
                #      ' - we can ignore it'.format(self.repeat_until, start))
                return []
            elif self.repeat_until < end:
                #print(self)
                #print('repeat until {} is before end {}'
                #      ' - adjusting range'.format(self.repeat_until, end))
                end = self.repeat_until

        if start <= self.date <= end:
            dates.add(self.date)

        if self.repeat_yearly:
            d = self.date.replace(year=start.year)
            while start <= d <= end:
                dates.add(d)
                d = d.replace(year=d.year+1)

        if self.repeat_every_N_days:
            for n in sorted(self.repeat_every_N_days):
                dt = datetime.timedelta(days=n)
                d = self.date + dt
                while start <= d <= end:
                    dates.add(d)
                    d = d + dt

        # XXX This needs testing
        if self.repeat_on_Nth_of_month:
            for n in sorted(self.repeat_on_Nth_of_month):
                d = self.date
                while True:
                    if d.month < 12:
                        d = d.replace(month=d.month+1)
                    else:
                        d = d.replace(month=1, year=d.year+1)
                    if d > end:
                        break
                    if d >= start:
                        dates.add(d)

        if self.repeat_ordinal:
            for index, day_name in sorted(self.repeat_ordinal):
                d = calc_ordinal_day(self.date, index, day_name)
                # We know that if they asked for the fifth day of a given
                # name, it may or may not occur in this month
                if d:
                    dates.add(d)

        if self.not_on:
            for date, reason in sorted(self.not_on):
                if date in dates:
                    dates.remove(date)

        if not dates:
            return []

        # We don't have many colon substitution words, so we can just deal
        # with them "by hand"
        text = self._text
        if ':year' in self.colon_words:
            text = text.replace(':year', str(self.date.year))

        things = []
        for date in dates:
            if ':age' in self.colon_words:
                text = text.replace(':age', str(date.year - self.date.year))
            things.append((date, text, self))

        return things

def colon_what(colon_word, words):
    """A simple utility to re-join :<word> commands for error reporting.
    """
    if words:
        return '{} {}'.format(colon_word, ' '.join(words))
    else:
        return colon_word

def colon_event_every(colon_word, words, start):
    """Every <something>

    <something> can be:

        * <day-name> -- every <day-name> in each week, ":every Mon"
        * <month-name> <day> -- every equivalent date, ":every Dec 25"
        * day <day> -- every <date> in each month, ":every day 8"

    Returns an appropriate Event.
    """
    if len(words) == 1:
        # :every <day-name>
        day_name = words[0].capitalize()
        if day_name not in DAYS:
            raise GiveUp('Expected a day name (Mon..Fri), not {}\n'
                         'in {!r}'.format(day_name, colon_what(colon_word, words)))
        # Work relative to the *start* date
        date = day_after_date(start, day_name, True)
        event = Event(date)
        event.repeat_every_N_days.add(7)
        # We could arguably have asked to repeat on every <day-name>
        # explicitly, but since we're creating a new Event, we might
        # as well just leverage the 7 day repeat

        event.colon_date = colon_what(colon_word, words)
        return event

    if len(words) != 2:
        raise GiveUp('Expected one of:\n'
                     '  :every <day-name>\n'
                     '  :every <month-name> <day>\n'
                     '  :every day <day>\n'
                     'not {!r}'.format(colon_what(colon_word, words)))

    if words[0] == 'day':
        # :every day <day>
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
            date = start.replace(day=day)
        except ValueError:
            date = start.replace(day=day, month=start.month+1)
        event = Event(date)
        event.repeat_on_Nth_of_month.add(day)

    elif words[0].capitalize() in MONTH_NUMBER:
        # :every <month-name> <day>
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
            date = start.replace(day=day, month=month)
        except ValueError:
            date = datetime.date(day=day, month=month, year=start.year+1)
        event = Event(date)
        event.repeat_yearly = True

    else:
        raise GiveUp('Expected one of:\n'
                     '  :every <day-name>\n'
                     '  :every <month-name> <day>\n'
                     '  :every day <day>\n'
                     'not {!r}'.format(colon_what(colon_word, words)))

    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_first(colon_word, words, start):
    """The first <something>

    <something> can be:

        * <day-name> -- the first day of that name in a month, ":first Mon"
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, 1, day_name)
    event = Event(date)
    event.repeat_ordinal.add((1, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_second(colon_word, words, start):
    """The second <something>

    <something> can be:

        * <day-name> -- the second day of that name in a month
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, 2, day_name)
    event = Event(date)
    event.repeat_ordinal.add((2, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_third(colon_word, words, start):
    """The third <something>

    <something> can be:

        * <day-name> -- the third day of that name in a month
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, 3, day_name)
    event = Event(date)
    event.repeat_ordinal.add((3, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_fourth(colon_word, words, start):
    """The fourth <something>

    <something> can be:

        * <day-name> -- the fourth day of that name in a month
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, 4, day_name)
    event = Event(date)
    event.repeat_ordinal.add((4, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_fifth(colon_word, words, start):
    """The fifth <something> (maybe this will be useful sometime)

    <something> can be:

        * <day-name> -- the fifth day of that name in a month

    NB: May return None if there is no fifth day of that name in this month
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, 5, day_name)
    if date:
        event = Event(date)
        event.repeat_ordinal.add((5, day_name))
        event.colon_date = colon_what(colon_word, words)
        return event
    else:
        return None

def colon_event_last(colon_word, words, start):
    """The last <something>

    <something> can be:

        * <day-name> -- the last day of that name in a month, "last Mon"
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()

    first_weekday, month_len = calendar.monthrange(start.year, start.month)
    date = calc_ordinal_day(start, -1, day_name)
    event = Event(date)
    event.repeat_ordinal.add((-1, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_lastbutone(colon_word, words, start):
    """The last but one (penultimate) <something>

    <something> can be:

        * <day-name> -- the last but one day of that name in a month
    """
    if len(words) != 1:
        raise GiveUp('Expected a day name, in {}'.format(
            colon_what(colon_word, words)))
    elif words[0].capitalize() not in DAYS:
        raise GiveUp('Expected a day name, not {!r}. in {}'.format(
            words[0], colon_what(colon_word, words)))

    day_name = words[0].capitalize()
    date = calc_ordinal_day(start, -2, day_name)
    date = day_before_date(a_week_before_end, day_name, True)
    event = Event(date)
    event.repeat_ordinal.add((-1, day_name))
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_easter(colon_word, words, start):
    """A date related to Easter

    <something> can be 'Fri', 'Sat', 'Sun', 'Mon'. Alternatively, it can be
    a positive or negative number, for days relative to Easter Sunday - thus
    colon_event_easter(-1) is the same a colon_event_easter('Sat') -
    followed by a year.

    For instance, ":easter Fri 2013" or ":easter -10 1990"
    """
    if len(words) != 2:
        raise GiveUp('Expected one of:\n'
                     '  :easter Fri|Sat|Sun|Mon <year>\n'
                     '  :easter <offset> <year>\n'
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
                         '  :easter Fri|Sat|Sun|Mon <year>\n'
                         '  :easter <offset> <year>\n'
                         'not {!r}\n'
                         'Error reading <offset>, {}'.format(colon_what(colon_word, words), e))

    try:
        year = int(words[1])
    except ValueError as e:
        raise GiveUp('Expected one of:\n'
                     '  :easter Fri|Sat|Sun|Mon <year>\n'
                     '  :easter <offset> <year>\n'
                     'not {!r}\n'
                     'Error reading <year>, {}'.format(colon_what(colon_word, words), e))

    easter = calc_easter(year)
    date = easter + datetime.timedelta(days=offset)

    event = Event(date)
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_event_weekmagic(colon_word, words, start):
    """A day relative to a date

    * <something> 'after' <year> <month-name> <day> [<day-name>]
    * <something> 'before' <year> <month-name> <day> [<day-name>]
    * <something> 'on-or-after' <year> <month-name> <day> [<day-name>]
    * <something> 'on-or-before' <year> <month-name> <day> [<day-name>]

    where <something> is a day name, or 'weekday', or 'weekend'
    """
    try:
        day_name = colon_word[1:]
        when = words[0]
        date_part = ' '.join(words[1:])
    except IndexError:
        raise GiveUp('Expected one of:\n'
                     '  :<something> before <year> <mon> <day> [<nam>]\n'
                     '  :<something> after <year> <mon> <day> [<nam>]\n'
                     'not {!r}'.format(colon_what(colon_word, words)))

    if day_name.capitalize() in DAYS:
        day_name = day_name.capitalize()
    elif day_name not in ('weekend', 'weekday'):
        raise GiveUp('Unexpected {!r}, expected one of:\n'
                     '  :<something> before <year> <mon> <day> [<nam>]\n'
                     '  :<something> after <year> <mon> <day> [<nam>]\n'
                     'where <something> is Mon..Sun or weekday or weekend\n'
                     'not {!r}'.format(day_name, colon_what(colon_word, words)))

    eventlet = parse_date(date_part, start,
                          'it does not make sense inside {}'.format(
                           colon_what(colon_word, words)))
    date = eventlet.date

    if when not in ('before', 'after', 'on-or-before', 'on-or-after'):
        raise GiveUp('Unexpected {!r}, expected one of:\n'
                     '  :<something> [on-or-]before <year> <mon> <day> [<nam>]\n'
                     '  :<something> [on-or-]after <year> <mon> <day> [<nam>]\n'
                     'not {!r}'.format(when, colon_what(colon_word, words)))

    if day_name == 'weekend':
        if when == 'after':
            todays_day = DAYS[date.weekday()]
            if todays_day == 'Sat':
                day_name = 'Sun'
            elif todays_day == 'Sun':
                day_name = 'Sat'    # the next Saturday...
            else:
                day_name = 'Sat'
        elif when == 'on-or-after':
            todays_day = DAYS[date.weekday()]
            if todays_day == 'Sat':
                day_name = 'Sat'
            elif todays_day == 'Sun':
                day_name = 'Sun'    # the same day
            else:
                day_name = 'Sat'
        elif when == 'before':
            todays_day = DAYS[date.weekday()]
            if todays_day == 'Sat':
                day_name = 'Sun'    # the previous Sunday...
            elif todays_day == 'Sun':
                day_name = 'Sat'
            else:
                day_name = 'Sun'
        elif when == 'on-or-before':
            todays_day = DAYS[date.weekday()]
            if todays_day == 'Sat':
                day_name = 'Sat'    # the same day
            elif todays_day == 'Sun':
                day_name = 'Sun'
            else:
                day_name = 'Sun'
    elif day_name == 'weekday':
        if when == 'after':
            todays_day = DAYS[date.weekday()]
            if todays_day in ('Fri', 'Sat', 'Sun'):
                day_name = 'Mon'
            else:   # we know DAYS starts with Mon
                day_name = DAYS[date.weekday()+1]
        elif when == 'on-or-after':
            todays_day = DAYS[date.weekday()]
            if todays_day in ('Sat', 'Sun'):
                day_name = 'Mon'
            else:
                day_name = todays_day
        elif when == 'before':
            todays_day = DAYS[date.weekday()]
            if todays_day in ('Sat', 'Sun', 'Mon'):
                day_name = 'Fri'
            else:   # we know DAYS starts with Mon, but we already dealt with that
                day_name = DAYS[date.weekday()-1]
        elif when == 'on-or-before':
            todays_day = DAYS[date.weekday()]
            if todays_day in ('Sat', 'Sun'):
                day_name = 'Fri'
            else:
                day_name = todays_day

    if when == 'after':
        date = day_after_date(date, day_name)
    elif when == 'on-or-after':
        date = day_after_date(date, day_name, True)
    elif when == 'before':
        date = day_before_date(date, day_name)
    else:
        date = day_before_date(date, day_name, True)

    event = Event(date)
    event.colon_date = colon_what(colon_word, words)
    return event

def colon_condition_except(colon_word, event, words, start):
    """An exception condition.

    Applies to the preceding date line
    """
    text = ' '.join(words)
    parts = text.split(',')
    date_part = parts[0]
    rest = ','.join(parts[1:])
    eventlet = parse_date(date_part, start,
                          'it does not make sense inside {}'.format(
                          colon_what(colon_word, words)))
    date = eventlet.date
    event.not_on.add((date, rest))

def colon_condition_until(colon_word, event, words, start):
    """An ending condition.

    <something> is <year> <month-name> <day>, and signifies the last date
    for a repetitive event. If the date does not exactly match the
    recurring event's date, then the last event is the one before this
    date.

    Applies to the preceding date line
    """
    eventlet = parse_date(' '.join(words), start,
                          'it does not make sense inside {}'.format(
                           colon_what(colon_word, words)))
    date = eventlet.date
    if date < event.date:
        raise GiveUp('Date in {!r} is before main date {} {} {}'.format(
            colon_what(colon_word, words), event.date.year,
            MONTH_NUMBER[event.date.month], event.date.day))
    if event.repeat_until is None:
        event.repeat_until = date
    elif event.repeat_until > date: # This new date is earlier, so use it
        event.repeat_until = date

def colon_condition_weekly(colon_word, event, words, start):
    """Repeating weekly.

    'words' should be empty.

    Applies to the preceding date line
    """
    if words:
        raise GiveUp('Not expecting text after :weekly, in {!r}'.format(
            colon_what(colon_word, words)))
    event.repeat_every_N_days.add(7)

def colon_condition_fortnightly(colon_word, event, words, start):
    """Repeating fortnightly

    'words' should be empty.

    Applies to the preceding date line
    """
    if words:
        raise GiveUp('Not expecting text after :fortnightly, in {!r}'.format(
            colon_what(colon_word, words)))
    event.repeat_every_N_days.add(14)

def colon_condition_monthly(colon_word, event, words, start):
    """Repeating monthly

    'words' should be empty.

    Applies to the preceding date line
    """
    # Which is just the same as repeating on the same day each month
    event.repeat_on_Nth_of_month.add(event.date.day)

def colon_condition_every(colon_word, event, words, start):
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
    event.repeat_every_N_days.add(every)

def colon_condition_for(colon_word, event, words, start):
    """Repeat for <count> days or weekdays

    As in ":for 5 days" or ":for 10 weekdays"
    """
    if len(words) != 2 or words[1].lower() not in ('days', 'weekdays'):
        raise GiveUp("Expected ':repeat <num> days'\n"
                     'not {!r}'.format(colon_what(colon_word, words)))

    what = words[1].lower()
    try:
        count = int(words[0])
    except ValueError:
        raise GiveUp('Expected:\n'
                     '  :for <count> {}\n'
                     'not {!r}'.format(what, colon_what(colon_word, words)))
    if what == 'days':
        until = event.date + datetime.timedelta(days=count)
    else:
        # Hah - weekdays only
        one_day = datetime.timedelta(days=1)
        until = event.date
        while count > 0:
            until = until + one_day
            while until.weekday in (5, 6):
                event.not_on.add(until)
                until = until + one_day
            count -= 1
    if event.repeat_until is None:
        event.repeat_until = until
    elif event.repeat_until > until: # This new date is earlier, so use it
        event.repeat_until = until

colon_event_methods = {':every': colon_event_every,
                       ':first': colon_event_first,
                       ':second': colon_event_second,
                       ':third': colon_event_third,
                       ':fourth': colon_event_fourth,
                       ':fifth': colon_event_fifth,
                       ':last': colon_event_last,
                       ':lastbutone': colon_event_lastbutone,
                       ':easter': colon_event_easter,
                       ':weekend': colon_event_weekmagic,
                       ':weekday': colon_event_weekmagic,
                       ':mon': colon_event_weekmagic,
                       ':tue': colon_event_weekmagic,
                       ':wed': colon_event_weekmagic,
                       ':thu': colon_event_weekmagic,
                       ':fri': colon_event_weekmagic,
                       ':sat': colon_event_weekmagic,
                       ':sun': colon_event_weekmagic,
                      }

colon_condition_methods = {':except': colon_condition_except,
                           ':until': colon_condition_until,
                           ':weekly': colon_condition_weekly,
                           ':fortnightly': colon_condition_fortnightly,
                           ':monthly': colon_condition_monthly,
                           ':every': colon_condition_every,
                           ':for': colon_condition_for,
                          }

def yield_lines(lines):
    """Yield interesting lines.

    Returns lists of the form:

        lineno, [text, ...]

    Empty lines and comment lines are not returned. Indented lines have their
    indentation removed, and are returned as the '...'.

    For instance:

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
        >>> for line in yield_lines(lines):
        ...     print(line)
        (2, ['Line 2'])
        (3, ['Line 3', 'line 3 continued'])
        (5, ['Line 5'])
        (7, ['Line 7', 'line 7 continued', 'even more line 7'])

    but:

        >>> bad_lines = [' not line 1']
        >>> for line in yield_lines(bad_lines):
        ...     print(line)
        Traceback (most recent call last):
        ...
        GiveUp: Line 1 is indented, but follows the start of file

        >>> bad_lines = ['Line 1',
        ...              '# a comment',
        ...              '  not line 1',
        ...             ]
        >>> for line in yield_lines(bad_lines):
        ...     print(line)
        Traceback (most recent call last):
        ...
        GiveUp: Line 3 is indented, but follows a comment

        >>> bad_lines = ['Line 1',
        ...              '',
        ...              '  not line 1',
        ...             ]
        >>> for line in yield_lines(bad_lines):
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

def parse_date(date_part, start, not_yearly_reason=None):
    """Parse something we accept as a date, and return an Event for it.

    If 'not_yearly_reason', then a <year> <mon> <day> style date may not
    have an asterisk after the <year>. If this is not a "false" value, then
    it should be a string explaining why not...
    """
    # Check for a magic word
    words = date_part.split()
    if words[0][0] == ':':
        colon_word = words[0].lower()
        try:
            fn = colon_event_methods[colon_word]
        except KeyError:
            raise GiveUp('Unexpected ":" word as <date>, {!r}'.format(colon_word))
        event = fn(colon_word, words[1:], start)
    else:
        date, yearly = parse_year_month_day(date_part)
        event = Event(date)
        if yearly:
            if not_yearly_reason:
                raise GiveUp('The "yearly" asterisk is not allowed in {}\n'
                             '{}'.format(date_part, not_yearly_reason))
            event.repeat_yearly = True
    return event

def parse_event(first_lineno, first_line, more_lines, start):
    """Create an event from the lines describing it.
    """

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

    # Technically, I'd like <date> <comma> <space> <rest>, but it seems a bit
    # overpicky to enforce that. And it's probably best just to ignore leading
    # (and trailing) whitespace.
    rest = rest.strip()

    try:
        event = parse_date(date_part, start)
    except GiveUp as e:
        raise GiveUp('Error in line {}\n'
                     '{}\n'
                     '{}: {!r}'.format(first_lineno, e,
                                       first_lineno, first_line))
    event.text = rest

    this_lineno = first_lineno
    for text in more_lines:
        this_lineno += 1
        words = text.split()
        if words[0][0] == ':':
            colon_word = words[0].lower()
            try:
                fn = colon_condition_methods[colon_word]
                fn(colon_word, event, words[1:], start)
            except KeyError:
                raise GiveUp('Error in line {}\n'
                             'Unexpected ":" word as <condition>, {!r}\n{}: {!r}'.format(
                                 this_lineno, colon_word, this_lineno, text))
            except GiveUp as e:
                raise GiveUp('Error in line {}\n'
                             '{}\n'
                             '{}: {!r}'.format(this_lineno, e,
                                               this_lineno, text))
        else:
            raise GiveUp('Error in line {}\n'
                         'Indented line should be a <condition>, starting with a colon,\n'
                         '{}: {!r}'.format(this_lineno, this_lineno, text))
    return event

def parse_lines(lines, start):
    r"""Report on the given lines.

    For instance:

        >>> today=datetime.date(2013, 9, 29)
        >>> events = parse_lines(
        ...     [r'# This is a comment',
        ...      r'1960* Feb 18 Thu, Tibs is :age, born in :year',
        ...      r'2013 Sep 13 Fri, something # This is not a comment',
        ...      r'2013 Sep 14, another something',
        ...      r'  :every 4 days',
        ...      r':every Thu, @Thomas singing lesson',
        ...      r':weekday after 2013 Sep 28, Should be a Monday',
        ...      r':Mon after 2013 Sep 28, Should be the same',
        ...     ], today)
        >>> for event in (sorted(events)):
        ...    print(event)
        1960 Feb 18 Thu, Tibs is :age, born in :year
          :yearly
        2013 Sep 13 Fri, something # This is not a comment
        2013 Sep 14 Sat, another something
          :every 4 days
        :mon after 2013 Sep 28, Should be the same
        :weekday after 2013 Sep 28, Should be a Monday
        :every Thu, @Thomas singing lesson
          :every Thu

        >>> for event in (sorted(events)):
        ...    print(repr(event))
        1960 Feb 18 Thu, Tibs is :age, born in :year
          :yearly
          <colon-words> :age, :year
        2013 Sep 13 Fri, something # This is not a comment
        2013 Sep 14 Sat, another something
          :every 4 days
        2013 Sep 30 Mon, Should be the same
        2013 Sep 30 Mon, Should be a Monday
        2013 Oct  3 Thu, @Thomas singing lesson
          :every Thu
          <at-words> @thomas

    but:

        >>> parse_lines([r'Fred'], today)
        Traceback (most recent call last):
        ...
        GiveUp: Missing comma in line 1
        Unindented lines should be of the form <date>, <rest>
        1: 'Fred'

        >>> parse_lines([r'Fred,'], today)
        Traceback (most recent call last):
        ...
        GiveUp: No text after comma in line 1
        Unindented lines should be of the form <date>, <rest>
        1: 'Fred,'

        >>> parse_lines([r'Fred, Jim'], today)
        Traceback (most recent call last):
        ...
        GiveUp: Error in line 1
        Date must be <year>[*] <month-name> <day>
                  or <year>[*] <month-name> <day> <day-name>
        not 'Fred'
        1: 'Fred, Jim'
    """
    events = set()
    for first_lineno, this_lines in yield_lines(lines):
        event = parse_event(first_lineno, this_lines[0], this_lines[1:], start)
        events.add(event)
    return events

def parse_file(filename, start):
    """Report on the information in the named file.
    """
    with open(filename) as fd:
        events = parse_lines(fd, start)
    return events

def find_events(events, start, end, at_words=None):
    """Return (date, text, event) tuples for the events in our date range.
    """
    things = set()
    for event in events:
        things.update(event.get_dates(start, end, at_words))

    return things

def determine_dates(start=None, today=None, end=None):
    """Given the three "bounding" dates, validate and expand them.

    Returns actual values for start, yesterday, today, end
    """
    if today is None:
        today = datetime.date.today()

    yesterday = today - datetime.timedelta(days=1)

    if start is None:
        # Use "yesterday"
        start = yesterday

    if end is None:
        # Add four weeks
        end = datetime.date.fromordinal(today.toordinal() + 4*7)

    if start > today:
        raise GiveUp('Start date {} is after "today" {}'.format(
            start.isoformat(), today.isoformat()))

    if end < today:
        raise GiveUp('End date {} is before "today" {}'.format(
            end.isoformat(), today.isoformat()))

    if start > end:
        raise GiveUp('Start date {} is after end date {}'.format(
            start.isoformat(), end.isoformat()))

    return start, yesterday, today, end

def edit_file(filename):
    editor = os.environ.get('EDITOR', 'vim')
    print('Editing file {!r} with {}'.format(filename, editor))
    subprocess.call((editor, filename), close_fds=True)

def report_atwords(events, filename):
    """Given a sequence of Event instances, report on what @<words> are used.
    """
    at_words = set()
    count = {}
    for event in events:
        at_words.update(event.at_words)
        for word in event.at_words:
            count[word] = count.setdefault(word, 0) + 1
    print('The following @<words> are used in {}:'.format(filename))
    length = 0
    for word in at_words:
        if len(word) > length:
            length = len(word)
    format1 = '  {{:{}s}}     once'.format(length)
    format2 = '  {{:{}s}} {{:3d}} time{{}}'.format(length)
    for name in sorted(at_words):
        times = count[name]
        if times == 1:
            print(format1.format(name))
        else:
            print(format2.format(name, times, '' if times==1 else 's'))

def report_atword_days(things, at_words, start, end):
    """Report on how many days in 'things' have which at-words.
    """
    length = 0
    for word in at_words:
        if len(word) > length:
            length = len(word)
    count = {}
    for word in at_words:
        count[word] = 0
    for date, text, event in sorted(things):
        for word in at_words:
            if word in event.at_words:
                count[word] += 1
    # Is this really the best way to do this?
    format = '{{:{}s}} occurs on {{}} day{{}} within {{}} .. {{}}'.format(length)
    keys = sorted(count.keys())
    for word in keys:
        value = count[word]
        print(format.format(word, value, '' if value==1 else 's',
                            start, end))

def report_events(things, today):
    """Report on the days given us.
    """
    prev = None
    spacer = 4+1+3+1+2+1+3+1+1
    lines = []
    for date, text, event in sorted(things):
        weekday = date.weekday()
        if prev and weekday < prev:
            lines.append(' {}{}'.format(' '*spacer, '-'*(80-spacer)))
        # What order do I *actually* want the date written out in?
        # I think this is perhaps the most useful for looking at nearby
        # dates (when the day and date are most important)
        lines.append('{}{} {:2} {} {}, {}'.format(
            '*' if date == today else ' ',
            DAYS[date.weekday()],
            date.day,
            MONTH_NAME[date.month],
            date.year,
            text))
        prev = weekday
    page('\n'.join(lines))

def normalise_dir(dir):
    dir = os.path.expanduser(dir)
    dir = os.path.abspath(dir)
    dir = os.path.normpath(dir)     # remove double slashes, etc.
    return dir

def print_calendar_month(switch, args):
    try:
        year = args.pop(0)
    except IndexError as e:
        raise GiveUp('Expected -cal <year> <month> - missing <year>')
    try:
        month = args.pop(0)
    except IndexError as e:
        raise GiveUp('Expected -cal <year> <month> - missing <month>')
    month = _parse_month(word, month)
    year = _parse_int_year(word, year)
    calendar.prmonth(year, month)

def page(text):
    pager = os.environ.get('PAGER', 'more')
    try:
        path = os.environ.get('PATH', os.defpath)
        path = path.split(os.pathsep)
        for locn in path:
            locn = normalise_dir(locn)
            prog = os.path.join(locn, pager)
            if os.path.exists(prog):
                try:
                    proc = subprocess.Popen([prog],
                                            stdin=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                    proc.communicate(text)
                    return
                except OSError:
                    # We're not allowed to run it, or some other problem,
                    # so look for another candidate
                    continue
        # And if nothing else works, just print it out
        print(text)
    except IOError: # For instance, a pipe error due to "q" at the prompt
        pass

def _parse_int_day(switch, day):
    try:
        return int(day)
    except ValueError:
        raise GiveUp('Expected a date after {!r}, but day {!r} is not'
                     ' an integer'.format(switch, day))

def _parse_month(switch, mon):
    mon_name = mon.capitalize()
    if mon_name in MONTH_NUMBER:
        return MONTH_NUMBER[mon_name]
    try:
        return int(mon)
    except ValueError:
        raise GiveUp('Expected a date after {!r}, but month {!r} is not'
                     ' a 3-letter month name or an integer'.format(switch, mon))

def _parse_int_year(switch, year):
    try:
        return int(year)
    except ValueError:
        raise GiveUp('Expected a date after {!r}, but year {!r} is not'
                     ' an integer'.format(switch, year))

def get_cmdline_date(switch, args):
    today = datetime.date.today()
    try:
        text = args.pop(0)
    except IndexError:
        raise GiveUp('Expected a day or date after {!r}'.format(switch))

    parts = text.split('-')
    if len(parts) == 1:
        day = _parse_int_day(switch, parts[0])
        return today.replace(day=day)
    elif len(parts) == 2:
        day = _parse_int_day(switch, parts[0])
        month = _parse_month(switch, parts[1])
        return today.replace(day=day, month=month)
    elif len(parts) == 3:
        day = _parse_int_day(switch, parts[0])
        month = _parse_month(switch, parts[1])
        year = _parse_int_year(switch, parts[2])
        return datetime.date(year, month, day)
    else:
        raise GiveUp('Expected a day or date after {!r}, not {!r}'.format(switch, text))

def report(args):
    """Usage:

        ./report.py [<stuff>]

    <stuff> can be, in any order (although always evaluated left-to-right):

    -h              show this text (also, -help, --help, /?, /help)
    -h text         show help on the text that can go in the event file (also
                    works with -help text, etc)

    -for <date>     set the date to be used for "today". Otherwise, today's
                    actual date is used.
    -start <date>   set the date to be used as the start of the range to be
                    reported. Otherwise, the day before "today" is used.
    -end <date>     set the date to be used as the end of the range to be
                    reported. Otherwise, four weeks after "today" is used.

    -from <date>    synonym for -start <date>
    -to <date>      synonum for -end <date>

   In each of the switches that take a <date>, it may be any of:

       * <day>              - that day of this month
       * <day>-<month-name>
       * <day>-<month>
       * <day>-<month>-<year>
       * <day>-<month-name>-<year>

    -week           set the end date to a week after "today"
    -month          set the end date to a month after "today"
    -year           set the end date to a year after "today"

    -cal <year> <month>
                    print a simple calendar for the given month
    -today          print out todays date

    @<word>, ...    only include events that include each given @<word> in
                    their text (so if a sequence of events are tagged with
                    @work, and another with @holiday, and the command line
                    include @work @holiday, then *only* those events will
                    be reported).

    -count          for the @<words> specified, count how many events contain
                    them, and report that for each @<word>. This counts the
                    @<words> in the final list of events, so if we have:

                        :easter Fri 2013, @Eastercon
                            :for 4 days

                    and do -count over the period containing those dates, we
                    would expect to see:

                        @eastercon occurs on 4 days

    <filename>      the name of the file to read events from. The default
                    is "what.txt" in the same directory as this script.

    -edit           Edit the events file, using the editor named in the
                    EDITOR environment variable, or 'vim' by default.
                    This can be useful if the file is somewhere unobvious.

    -atwords        report on which @<words> are used in the events file.
    -at_words       synonim for -atwords
    -at-words       synonim for -atwords
    -tidy           output the event data as it was understood - this can be
                    useful for "tidying up" an event file, by outputting the
                    output text to a replacement file. Note, though, that any
                    comments will be lost, the order will likely be different,
                    and some subtleties may change. The default start date
                    with this command is 01-01-1900.
    -repr           output the event data with annotations - this is intended
                    for debugging the interpretation of said data. Again, the
                    default start date will be 01-01-1900.
    -doctest        run the internal doctests
    """

    filename = None
    show_comments = False
    action = 'report'
    today = datetime.date.today()
    start = None
    end = None
    at_words = set()

    while args:
        word = args.pop(0)
        if word in ('-h', '-help', '--help', '/?', '/help'):
            if args and args[0] == 'text':
                page(__doc__)
                return
            else:
                page(report.__doc__)
                return
        elif word == '-doctest':
            import doctest
            failures, tests = doctest.testmod()
            if failures:
                raise GiveUp('The light is RED')
            else:
                print('The light is GREEN')
            return
        elif word == '-tidy':
            action = 'tidy'
            # Use a very historical start date to try to sort the output nicely
            start = datetime.date(1900, 1, 1)
        elif word == '-repr':
            action = 'repr'
            # Use a very historical start date to try to sort the output nicely
            start = datetime.date(1900, 1, 1)
        elif word == '-for':
            today = get_cmdline_date(word, args)
        elif word == '-edit':
            action = 'edit'
        elif word == '-count':
            action = 'count'
        elif word in ('-atwords', '-at-words', '-at_words'):
            action = 'atwords'
        elif word == '-cal':
            # Print a calendar, for the current month or the named month
            # Format of date should be <year> <month>
            print_calendar_month(word, args)
            return
        elif word in ('-start', '-from'):
            start = get_cmdline_date(word, args)
        elif word in ('-end' '-to'):
            end = get_cmdline_date(word, args)
        elif word == '-today':
            print('Today is {} {} {} {}, {}'.format(DAYS[today.weekday()],
                today.day, MONTH_NAME[today.month], today.year, today))
            return
        elif word == '-week':
            end = today + datetime.timedelta(days=7)
        elif word == '-month':
            try:
                end = today.replace(day=day, month=start.month+1)
            except ValueError:
                end = today.replace(month=1, year=start.year+1)
        elif word == '-year':
            end = today.replace(year=start.year+1)
        elif word[0] == '-' and not os.path.exists(word):
            raise GiveUp('Unexpected switch {!r}'.format(word))
        elif word[0] == '@':
            at_words.add(word.lower())
        elif not filename:
            filename = word
        else:
            raise GiveUp('Unexpected argument {!r} (already got'
                         ' filename {!r}'.format(word. filename))

    start, yesterday, today, end = determine_dates(start, today, end)

    if not filename:
        this_file = __file__
        this_dir = os.path.split(this_file)[0]
        filename = os.path.join(this_dir, 'what.txt')

    if action == 'edit':
        edit_file(filename)
        return

    print('Reading events from {!r}'.format(filename))
    try:
        events = parse_file(filename, start)
    except GiveUp as e:
        raise GiveUp('Error reading file {!r}\n{}'.format(filename, e))

    if action == 'tidy':
        # Output a tidied up version of what the user wrote, albeit
        # losing any comments
        for event in sorted(events):
            print(str(event))
        return
    elif action ==  'repr':
        # Output the events for this timespan
        for event in sorted(events):
            print(repr(event))
        return
    elif action == 'atwords':
        # Report on what @<words> are in use
        report_atwords(events, filename)
        return

    things = find_events(events, start, end, at_words)

    if action == 'count':
        if not at_words:
            raise GiveUp('-count expects at least one @<word> to count days for')
        report_atword_days(things, at_words, start, end)

    elif action == 'report':
        report_events(things, today)

    print('\nstart {} .. yesterday {} .. today {} .. end {}'.format(start,
        yesterday, today, end))

if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        report(args)
    except GiveUp as e:
        print('ERROR: {}'.format(e))
        sys.exit(1)

# vim: set tabstop=8 softtabstop=4 shiftwidth=4 expandtab:
