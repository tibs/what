#! /usr/bin/env python2
"""Generate a readme.rst
"""

import os
from subprocess import check_output

import what

this_file = __file__
this_dir = os.path.split(this_file)[0]

introduction = """\
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
necessarily tested it there since Windows 98). It is written to use Python 2
because of the original limitations of the computers it was used on (see the
aforesaid mention of Windows, in particular). However, it *should* be
Python 3 compatible.
"""

def indent(text, indentation='  '):
    lines = text.split('\n')
    lines = ['{}{}'.format(indentation, line) for line in lines]
    return '\n'.join(lines)

with open(os.path.join(this_dir, 'README.rst'), 'w') as fd:

        fd.write(introduction)
        fd.write('\n')

        fd.write('Usage\n'
                 '=====\n'
                 '::\n\n')
        fd.write(indent(what.usage_text))
        fd.write('\n')

        fd.write(what.file_content_text)
        fd.write('\n')

        fd.write('Examples\n'
                 '========\n')

        fd.write('Given the following event file::\n\n')
        fd.write(indent(open(os.path.join(this_dir, 'what.txt')).read()))
        fd.write('\n')
        fd.write("and assuming that today's date is 3rd October 2013,"
                 "we see:\n")

        # Note we force the date used for "today", but don't report that
        text = check_output(['./what.py', '-for', '3-oct-2013', '-today'])
        fd.write('::\n\n  $ ./what.py -today\n')
        fd.write(indent(text))
        fd.write('\n\n')

        text = check_output(['./what.py', '-for', '3-oct-2013'])
        fd.write('::\n\n  $ ./what.py\n')
        fd.write(indent(text))
        fd.write('\n')

        text = check_output(['./what.py', '-for', '3-oct-2013', '@birthday', '@pubhol'])
        fd.write('::\n\n  $ ./what.py @birthday @pubhol\n')
        fd.write(indent(text))
        fd.write('\n')

        text = check_output(['./what.py', '-for', '3-oct-2013', '-atwords'])
        fd.write('::\n\n  $ ./what.py -atwords\n')
        fd.write(indent(text))
        fd.write('\n')

        fd.write(what.related_text)
        fd.write('\n')

# vim: set tabstop=8 softtabstop=4 shiftwidth=4 expandtab:
