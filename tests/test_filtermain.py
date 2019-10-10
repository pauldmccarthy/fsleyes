#!/usr/bin/env python
#
# test_filtermain.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import sys
import time

from unittest import mock

import wx

import fsleyes.filtermain as fmain



def test_filtermain():

    def fakemain(args=None):
        print('Gtk-Message: stdout')
        print('Nofilter: stdout')
        print('Gtk-Message: stderr', file=sys.stderr)
        print('Nofilter: stderr',    file=sys.stderr)
        return 0

    try:
        with mock.patch('fsleyes.main.main', fakemain):
            fmain.main()

    except SystemExit as e:
        assert e.code == 0
