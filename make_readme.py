#! /usr/bin/env python2
"""Generate a readme.rst
"""

import os
from subprocess import check_output

import what

this_file = __file__
this_dir = os.path.split(this_file)[0]

def indent(text, indentation='  '):
    lines = text.split('\n')
    lines = ['{}{}'.format(indentation, line) for line in lines]
    return '\n'.join(lines)

with open(os.path.join(this_dir, 'readme.rst'), 'w') as fd:

        fd.write('what.py - a simple event reporting script\n'
                 '=========================================\n\n')

        fd.write('Usage\n'
                 '-----\n')

        fd.write(what.report.__doc__)
        fd.write('\n')

        fd.write('The contents of the event file\n'
                 '------------------------------\n')

        fd.write(what.__doc__)
        fd.write('\n')

        fd.write('Examples\n'
                 '--------\n')

        # Note we force the date used for "today", but don't report that
        text = check_output(['./what.py', '-for', '4-oct-2013', '-today'])
        fd.write('::\n\n  $ ./what.py -today\n')
        fd.write(indent(text))
        fd.write('\n\n')

        text = check_output(['./what.py', '-for', '4-oct-2013'])
        fd.write('::\n\n  $ ./what.py\n')
        fd.write(indent(text))
        fd.write('\n')

        text = check_output(['./what.py', '-for', '4-oct-2013', '@birthday', '@pubhol'])
        fd.write('::\n\n  $ ./what.py @birthday @pubhol\n')
        fd.write(indent(text))
        fd.write('\n')

        text = check_output(['./what.py', '-for', '4-oct-2013', '-atwords'])
        fd.write('::\n\n  $ ./what.py -atwords\n')
        fd.write(indent(text))
        fd.write('\n')

# vim: set tabstop=8 softtabstop=4 shiftwidth=4 expandtab:
