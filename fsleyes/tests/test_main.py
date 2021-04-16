#!/usr/bin/env python
#
# test_main.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import time
import threading
from unittest import mock

import fsleyes.main       as fm
import fsleyes.filtermain as ffm
import fsleyes.version    as fv
import fsl.utils.tempdir as tempdir

from fsleyes.tests import CaptureStdout


def test_version():

    capture  = CaptureStdout()
    exitcode = -1

    try:
        with capture:
            fm.main(['-V'])

    except SystemExit as e:
        exitcode = e.code

    expected = 'fsleyes/FSLeyes version {}'.format(fv.__version__)

    assert exitcode == 0
    assert capture.stdout.strip() == expected


def test_help():

    capture  = CaptureStdout()
    exitcode = -1

    try:
        with capture:
            fm.main(['-h'])

    except SystemExit as e:
        exitcode = e.code

    # only checking the first line of output
    expected = 'FSLeyes version {}'.format(fv.__version__)
    assert exitcode == 0
    assert capture.stdout.split('\n')[0].strip() == expected

    capture.reset()
    try:
        with capture:
            fm.main(['-fh'])

    except SystemExit as e:
        exitcode = e.code

    assert exitcode == 0
    assert capture.stdout.split('\n')[0].strip() == expected


def test_filtermain():

    threads = [mock.MagicMock()] * 3

    with mock.patch('fsleyes.filtermain.filter_stream',
                    return_value=threads):
        try:
            ffm.main(['-V'])
        except SystemExit as e:
            assert e.code == 0

        try:
            ffm.main(['-h'])
        except SystemExit as e:
            assert e.code == 0


def test_filter_stream():

    die = threading.Event()

    with tempdir.tempdir():

        with open('stream.txt', 'wt') as f:

            rt, wt, al = ffm.filter_stream(f, die, filters=[r'skip this'])

            al.wait()

            f.write('skip this 1\n')
            f.write('keep this 1\n')
            f.write('skip this 2\n')
            f.write('keep this 2\n')
            f.write('skip this 3\n')

            die.set()

        rt.join()
        wt.join()

        exp = ['keep this 1',
               'keep this 2']
        exp = '\n'.join(exp)

        with open('stream.txt', 'rt') as f:
            got = f.read().strip()

        assert exp == got
