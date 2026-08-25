#!/usr/bin/env python
#

import time
from unittest import mock

import fsleyes.filtermain as fmain


def mock_main(args):
    time.sleep(1)
    print('one')
    time.sleep(1)
    print('two')
    print('Failed to connect to session manager') # should be filtered
    time.sleep(1)
    print('three')
    time.sleep(1)
    return 0


def test_filtermain():
    with mock.patch('fsleyes.main.main', mock_main):
        try:
            fmain.main()
        except SystemExit as e:
            assert e.code == 0
