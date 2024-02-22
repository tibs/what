=========================================
what.py - a simple event reporting script
=========================================

Introduction
============
I wanted a tool that would allow me to add events to a text file, and view
those which are upcoming, or near a particular date. I couldn't find anything
that quite did what I wanted, so I wrote something for myself. As such, it
doesn't attempt to be an all-singing, all-dancing solution - it just does
those things I have needed it to do.

The way I use it is to keep a copy of ``what.py`` in my Dropbox folder, with
the ``what.txt`` file that defines the events next to it. This gives me a
crude way of having the event information available on multiple computers.
That is also why it is one monolithic script, instead of being nicely arranged
as a proper package.

The script runs on Linux and Mac, and should run on Windows (although I've not
necessarily tested it there since Windows 98). It was written to use Python 2
because of the original limitations of the computers it was used on (see the
aforesaid mention of Windows, in particular). However, it *should* be
Python 3 compatible, and seemed to work when I gave it a quick try recently.

  (My need for this tool rather went away, so it hasn't been used since, gosh,
  2017!)

Usage
=====
::

      ./report.py [<stuff>]
  
  <stuff> can be, in any order (although always evaluated left-to-right):
  
  -h              show this text (also, -help, --help, /?, /help)
  -h text         show help on the text that can go in the event file (also
                  works with -help text, etc)
  -h related      show some information on related programs that I ended up
                  not quite using
  
  -for <date>     set the date to be used for "today". Otherwise, today's
                  actual date is used.
  -start <date>   set the date to be used as the start of the range to be
                  reported. Otherwise, the day before "today" is used.
  -end <date>     set the date to be used as the end of the range to be
                  reported. Otherwise, four weeks after "today" is used.
  
  -around <date>  set <start> a fortnight before <date>, <end> a fortnight
                  after, and <today> to <date>.
  
  -from <date>    synonym for -start <date>
  -to <date>      synonum for -end <date>
  
  In each of the switches that take a <date>, it may be any of:
  
     * <day>              - that day of this month
     * <day>-<month-name>
     * <day>-<month>
     * <day>-<month>-<year>
     * <day>-<month-name>-<year>
  
  -w, -week       set the end date to a week after "today"
  -m, -month      set the end date to a month after "today"
  -2m, -2months   set the end date to two months after "today"
  -3m, -3months   set the end date to two months after "today"
                  ...and so on up to 11m
  -y, -1y, -year  set the end date to a year after "today"
  -2y             ditto for 2 years
  
  -christmas      report on the month around Christmas (of this year)
  -xmas           the same
  -easter         report on the month around Easter, of this year or of next
                  year, depending on whether we're more than a fortnight after
                  this Easter
  -this-year      report on this year, from jan-01 through dec-31
  
  -cal            print a simple calendar for this month
  -cal <mon>      print a simple calendar for month <mon> of this year
  -cal <mon> <y>  print a simple calendar for month <mon> of year <y>
  -today          print out todays date
  
  @<word>         only include events that include this @<word> in their text.
                  Multiple @<words> may be specified. So if some events are
                  tagged with @work, and some with @holiday, and the command line
                  includes @work and @holiday, then only events that contain
                  either @work and/or @holiday in their text will be reported).
                  (But see -count, which changes how the @<words> are used.)
  
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
  
  -edit [<prog>]  Edit the events file. If <prog> is given, then it should be the
                  editor to use (e.g., gvim or /usr/bin/sed). Otherwise the
                  editor named in the EDITOR environment variable will be used,
                  and if that is not set or cannot be found, 'vim' will be tried.
                  This can be useful if the file is somewhere unobvious.
  
  -nopage         Don't page the output of the list of events (only the "default"
                  output of events is paged, and then only if necessary)
  -nobold         Don't try to enbolden the current date. Useful if piping
                  to a file.
  -noweek         Don't put the week number at the start of each event line.
  
  -atwords        report on which @<words> are used in the events file.
  -at_words       synonym for -atwords
  -at-words       synonym for -atwords
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
  
The contents of the event file
==============================

Comments and empty lines
------------------------
Comments start with '#' and end at end-of-line.

Empty lines (lines containing only whitespace and/or comments) are ignored.

Events are specified by a date line, possibly followed by continuation lines
which qualify how the events is repeated.

Date lines
----------
Date lines are formed as::

    <date>, <text>

where <date> may be:

    * <yyyy> <mon> <day>
    * <yyyy> <mon> <day> <nam>
    * <yyyy>* <mon> <day>
    * <yyyy>* <mon> <day> <nam>
    * <colon-date>

<yyyy> is a four digit year number (e.g., '2013'), <mon> is a three character
(English) month abbreviation (case ignored, e.g. 'Jan' or 'dec' or even 'dEC'),
<day> is the day of the month ('1' through '31') and <nam> is a three character
day name (again, case ignored, e.g., 'Mon' or 'fri'). Dates with a day name are
always checked for correctness.

If the year has an asterisk immediately following, then the date means "every
year on this date, starting with this particular date". This is most useful for
anniversaries (e.g., birthdays).

A <colon-date> starts with a <colon-word>, a word that starts with a colon
and continues with alphanmeric characters. The case of a <colon-word> never
matters. A <colon-date> may be any of:

* :every <nam> -- meaning every week on that day, ':every Mon'
* :every <mon> <day> -- meaning every equivalent date, ':every Dec 25'.
  If the selected day is Feb 29, and that doesn't exist this year, then
  it will be ignored for this year.
* :every day <day> -- every month on that date, ':every day 8'.
  Note that this will not set an event in months which do not have that
  date.
* :first <nam> -- the first day of that name in each month, ':first Mon'
* :second <nam> -- the second day of that name in each month
* :third <nam>
* :fourth <nam>
* :fifth <nam>
* :last <nam> -- the last day of that name in each month
* :lastbutone <nam> -- the penultimate day of that name in each month
* :easter <nam> [<year>] -- where <nam> is 'Fri', 'Sat', 'Sun' or 'Mon'
  ('easter Fri' means the Friday of Easter in that current year), or
* :easter <index> [<year>], where <index> is relative to Easter Sunday, so
  ':easter -1 2013' would mean the same as ':easter Sat 2013'.
  case, if the <year> is omitted, then the "start" year is used, and the
  event is set to repeat each Easter on that (relative) day. Note that
  if a ':easter' event is followed by ':yearly', then that iseachthe meaning
  it has, a repetition on that day relative to Easter, not a repetition of
  that *particular* date.

Also, it is possible to select a day before or after a particular event,
using one of:

    * :<day-specifier> before <date>
    * :<day-specifier> after <date>
    * :<day-specifier> on-or-before <date>
    * :<day-specifier> on-or-after <date>

where <day-specifier> is one of:

    * <day> -- i.e., Mon..Sun, case ignored
    * weekend -- meaning the "nearest" Sat or Sun in the given direction
    * weekday -- meaning the "nearest" Mon .. Fri in the given direction

for instance::

    :Mon before 2013 dec 25
    :weekend after 2013 dec 25 wed
    :Sat after :first Tue

(although the utility of using <colon-dates> in this context may be debatable).

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

<text> is free text, and is left as-is, except that the <colon-words>:

    * :age
    * :year

(and maybe eventually other quantities) will be replaced with the appropriate
value. Again, their case does not matter. Any other <colon-words> within
<text> are left alone.

<text> may also contain @<word> words, which allow particular events to be
selected from the command line.

An example of both of these would be::

  1929* Sep 27, @Birthday: @Fred is :age, born in :year

'#' characters in <text> do not start a comment.

Continuation lines - qualifying the event
-----------------------------------------
Continuation lines follow date lines, and are indented. The amount of
indentaton is not significant, and is not checked (although it looks nicer if
it matches). A continuation line must start with a <colon-word>.The
<colon-words> in continuation lines modify the preceding date line, as follows:

* :except <date>, <reason>] -- the preceding event does not occur on this
  particular day. This is the only colon word to take a ", <text>" after its
  date. At the moment, that text (<reason>) is just discarded.
* :from <date> -- the preceding event starts repetition on or after this date.
  This is intended for use with dates such as ':every Tue' - it makes no sense
  to use it with a <date> that already has an explicit day/month/year.
  Specifying ':from' does not, of itself, imply any repetition.
* :until <date> -- the preceding event continues until this date. If this date
  does not exactly match the recurrence of the preceding event, then the last
  occurrence is the one before this date. Note that if you specify ':until'
  but don't specify an actual repeat frequency, it will assume daily.
  If you specify multiple ':until' conditions, the earliest will end up being
  used.
* :weekly -- the preceding event occurs weekly, i.e., every week on the
  same day.
* :fortnightly -- the preceding event occurs fortnightly, i.e., every
  other week on the same day.
* :monthly -- the preceding event occurs monthly, i.e., every month on the
  same date.
* :yearly -- the preceding event occurs yearly. This is exactly equivalent to
  putting an asterisk after the <year> in the date line. Note that for
  ':easter' dates, this means repeating on the same day relative to Easter,
  not the same particular date.
* :every <count> days -- the preceding event occurs every <count> days,
  starting on the original date. ':every 7 days' is thus the same as
  ':weekly'. I apologise in advance for ':every 1 days'.
* :for <count> days -- for that many days, including the original date. This
  actually gets turned into an appropriate ':until <date>'.
* :for <count> weekdays -- for that many Mon..Fri days. Note that if the
  original date is a Sat or Sun, it will have already been added as an event
  - this only affects dates *after* that. It works exactly as if it were a
  combination of an appropriate ':until <date>' with the internal weekend
  days excluded using ':except <weekend-day>'.

Note that it is not defined what happens if you specify contradictory or
clashing conditions - for instance saying ':until <some-date>' and then
also saying ':for 5 weekdays', when those two do not have an identical effect.

Possible future developments
----------------------------
It might be nice if other conditions (than ':except') also allowed a text
part in their line. It might also be nice if something were done with this
text (although what I'm not sure - for ':except' maybe one would have a
command line switch that enabled reporting that an event was *not* happening,
giving the <reason>).

It would be nice if ':except' and ':until' would also accept a date of the
form <mon> <day>, and work out the year based upon the year of the date line
that they are qualifying.

I would like to be able to say::

    :Friday before Dec 23 2013
       :yearly

to indicate that this occurs on the Friday before Dec 23 each year, much as is
done for ':easter'.

It might be nice to allow more than one condition on a continuation line,
perhaps with some separating punctuation - although I'm not 100% sure of this
one.

On the command line, it might be nice if one said '-for <day> <mon>' or
'-for <day> <mon> <year>' instead of needing all the hyphens inside the
dates. That would, of course, make command line parsing that bit more
complicated.

Examples
========
Given the following event file::

  1980* Oct  9, @Birthday: @Alfred is :age, born in :year
  1983* Jan 29, @Birthday: @Bethany is :age, born in :year
  2001* Oct  7, @Birthday: @Charles is :age, born in :year
  
  # From https://www.gov.uk/bank-holidays
  2014 Jan  1 Wed, @pubhol New Year’s Day
  :easter Fri 2014, @pubhol Good Friday
  :easter Mon 2014, @pubhol Easter Monday
  2014 May  5 Mon, @pubhol Early May bank holiday
  2014 May 26 Mon, @pubhol Spring bank holiday
  2014 Aug 25 Mon, @pubhol Summer bank holiday
  2014 Dec 25 Thu, @pubhol Christmas Day
  2014 Dec 26 Fri, @pubhol Boxing Day
  
  # -----------------------------------------------------------------------------
  # Regular events
  :easter Fri 2013, Eastercon
  
  :every dec 25, Christmas Day
  :every dec 26, Boxing Day
  
  :every Thu, 17:00 @Charles Singing lesson 
    :except 2013 Oct 3, Doing something else
  
  :first Tue, @Bethany Ipswich
  :third Tue, @Bethany Ipswich
  :first Tue, 19:30 @Alfred Python User Group
  
  # Full backups happen overnight on the first Saturday of each month
  :first Sat, @Alfred Full Backup
  
  # -----------------------------------------------------------------------------
  # And actual events
  2013 Oct  2 Wed, Daniel visiting
  2013 Oct 25 Fri, 10:00..17:00, Newmarket (Christmas) Craft Fair
       :for 2 days
  2013 Oct 27 Sun, 10:00..16:00, Newmarket (Christmas) Craft Fair
  
  
and assuming that today's date is 3rd October 2013,we see:
::

  $ ./what.py -today
  Today is Thu 3 Oct 2013, 2013-10-03
  

::

  $ ./what.py
  Reading events from './what.txt'
  40  Wed  2 Oct 2013, Daniel visiting
  40  Sat  5 Oct 2013, @Alfred Full Backup
                       ----------------------------------------------------------
  41  Mon  7 Oct 2013, @Birthday: @Charles is 12, born in 2001
  41  Wed  9 Oct 2013, @Birthday: @Alfred is 33, born in 1980
  41  Thu 10 Oct 2013, 17:00 @Charles Singing lesson
                       ----------------------------------------------------------
  42  Tue 15 Oct 2013, @Bethany Ipswich
  42  Thu 17 Oct 2013, 17:00 @Charles Singing lesson
                       ----------------------------------------------------------
  43  Thu 24 Oct 2013, 17:00 @Charles Singing lesson
  43  Fri 25 Oct 2013, 10:00..17:00, Newmarket (Christmas) Craft Fair
  43  Sat 26 Oct 2013, 10:00..17:00, Newmarket (Christmas) Craft Fair
  43  Sun 27 Oct 2013, 10:00..16:00, Newmarket (Christmas) Craft Fair
                       ----------------------------------------------------------
  44  Thu 31 Oct 2013, 17:00 @Charles Singing lesson
  
  start 2013-10-02 .. yesterday 2013-10-02 .. today 2013-10-03 .. end 2013-10-31
  
::

  $ ./what.py @birthday @pubhol
  Reading events from './what.txt'
  41  Mon  7 Oct 2013, @Birthday: @Charles is 12, born in 2001
  41  Wed  9 Oct 2013, @Birthday: @Alfred is 33, born in 1980
  
  start 2013-10-02 .. yesterday 2013-10-02 .. today 2013-10-03 .. end 2013-10-31
  
::

  $ ./what.py -atwords
  Reading events from './what.txt'
  The following @<words> are used in ./what.txt:
    @alfred     3 times
    @bethany    3 times
    @birthday   3 times
    @charles    2 times
    @pubhol     8 times
  
Other tools I considered
========================
There were three tools I seriously looked into using before I wrote 'what'.
I liked them all, although none of them ended up being quite what I wanted.
I mention them here because if you're looking at this, one of them is probably
what you actually want (since 'what' is really only written for my own
purposes).

My reqirements were basically: a command line tool, capable of running on at
least Linux, Mac and Windows (Android would be nice too), able to share the
calendar file (using Dropbox would be OK), allowing at least things like "the
first Tuesday of every month", and prferably using a data file that is editable
with a plain text editor (e.g., Vim).

  (By the way, I do know about org-mode, and it's not really what I want.)

So, in the order I found them, I looked at the following, all of which I
really liked, although for differing reasons.

taskwarrior
-----------
http://taskwarrior.org

This is a very capable tool. It has "customizable reports, charts, GTD
features, device synching, documentation, extensions, themes, holiday files
and much more."

It does a lot more than I support here, and is under very active delopment.
The tutorial is very good, although for a tool of this capability I'd also
rather like a reference document. Whilst the events data is held in text files,
they're not really intended for hand-editing - indeed, to do so would be to
miss the point of the tools provided.

todo.txt
--------
http://todotxt.com/

This is a beautifully presented tool, and works across the greatest number of
platforms. It keeps its text file nice and simple, but still manages to get
a great deal done. As it implies, it's primarily aimed at task management,
and this meant it didn't really aim quite where I wanted. I tried using it
for a little bit, and decided it wasn't quite for me, but doing so meant I
had a better idea of what I *did* want.

when
----
http://www.lightandmatter.com/when/when.html

This is the tool I very nearly used. It's a direct inspiration for 'what',
although its developer should not be blamed with how I've treated his idea.
A basic 'when' data file is quite close to a basic 'what' event file. In
particular, the ideas that <year>* means repeating yearly, that one should
be able to show 'age' and 'year' of birthdays/anniversaries, and that dates
relative to Easter are useful are all taken from 'when'.

'when', of course, copes with other people's wishes in a way that 'what' does
not - it supports day and month names in many languages, it knows about more
than one date for Easter, and it allows things such as changing the first day
of the week.

Should I have learnt enough Perl to be able to contribute to 'when', and
try to get the features I wanted added in? Perhaps, but in the end writing
this program myself was more fun...

