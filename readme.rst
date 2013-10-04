what.py - a simple event reporting script
=========================================

Usage
-----
Usage:

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
------------------------------
A "what happens when" utility, vaguely inspired by "when"

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
      **Ideally, it would also allow <month> <day>, eliding the year.**
    * :until <year> <mon> <day> [<dat>] -- the preceding event continues until
      this date. If this date does not exactly match the recurrence of the
      preceding event, then the last occurrence is the one before this date.
      Note that this does *not* itself cause repetition - it just limits
      whatever repetition is (also) specified.
       **Ideally, it would also allow <month> <day>, eliding the year.**
    * :weekly -- the preceding event occurs weekly, i.e., every week on the
      same day.
    * :fortnightly -- the preceding event occurs fortnightly, i.e., every
      other week on the same day.
    * :monthly -- the preceding event occurs monthly, i.e., every month on the
      same date.
    * :yearly -- the preceding event occurs yearly, on the same date.
    * :every <count> days -- the preceding event occurs every <count> days,
      starting on the original date. ':every 7 days' is thus the same as
      ':weekly'. I apologise in advance for ':every 1 days'.
    * :for <count> days -- for that many days, including the original date
    * :for <count> weekdays -- for that many Mon..Fri days. Note that if the
      original date is a Sat or Sun, it/they won't count to the total. Works
      exactly as if it were a combination of ':for <n> days' with the internal
      weekend days excluded using ':except <weekend-day>'.

The case of colon-words is ignored.

Examples
--------
::

  $ ./what.py -today
  Today is Fri 4 Oct 2013, 2013-10-04
  

::

  $ ./what.py
   Tue  1 Oct 2013, 19:30 CamPUG
   Tue  1 Oct 2013, @Ipswich
   Thu  3 Oct 2013, 17:00 @Singing lesson
   Sat  5 Oct 2013, @work Full Backup
                    ---------------------------------------------------------------
   Wed  9 Oct 2013, @Birthday: @Someone is 53, born in 1960
   Thu 10 Oct 2013, 17:00 @Singing lesson
                    ---------------------------------------------------------------
   Tue 15 Oct 2013, @Ipswich
   Thu 17 Oct 2013, 17:00 @Singing lesson
   Thu 24 Oct 2013, 17:00 @Singing lesson
   Fri 25 Oct 2013, 10:00..17:00, Newmarket (Christmas) Craft Fair
   Sat 26 Oct 2013, 10:00..17:00, Newmarket (Christmas) Craft Fair
   Sun 27 Oct 2013, 10:00..16:00, Newmarket (Christmas) Craft Fair
                    ---------------------------------------------------------------
   Thu 31 Oct 2013, 17:00 @Singing lessonReading events from './what.txt'
  
  start 2013-10-03 .. yesterday 2013-10-03 .. today 2013-10-04 .. end 2013-11-01
  
::

  $ ./what.py @birthday @pubhol
   Wed  9 Oct 2013, @Birthday: @Someone is 53, born in 1960Reading events from './what.txt'
  
  start 2013-10-03 .. yesterday 2013-10-03 .. today 2013-10-04 .. end 2013-11-01
  
::

  $ ./what.py -atwords
  Reading events from './what.txt'
  The following @<words> are used in ./what.txt:
    @birthday     once
    @ipswich    2 times
    @pubhol    19 times
    @singing      once
    @someone      once
    @work         once
  
