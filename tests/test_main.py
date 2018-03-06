#!/usr/bin/env python
#
# test_main.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsleyes.main as fm


def test_version():
    # not crashing means the test passes!
    fm.main('-V')
