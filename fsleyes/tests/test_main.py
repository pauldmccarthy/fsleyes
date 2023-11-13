#!/usr/bin/env python
#
# test_main.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import textwrap as tw
import time
import threading
from unittest import mock

from   fsl.utils.tempdir  import tempdir
import fsleyes.main       as     fm
import fsleyes.filtermain as     ffm
import fsleyes.version    as     fv


from fsleyes.tests import (CaptureStdout,
                           mockSettingsDir,
                           mockSiteDir)

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

    with tempdir():

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


def test_default_arguments():

    userArgs = tw.dedent("""
    # arg 1
    --autoDisplay
    # arg 2
    -no
    """).strip()

    siteArgs = tw.dedent("""
    # arg 1
    --hideOrientationWarnings
    # arg 2
    -nb
    """)

    # user args, site args
    tests = [(None,     siteArgs),
             (userArgs, None),
             (userArgs, siteArgs)]

    for userArgs, siteArgs in tests:
        with mockSiteDir() as siteDir, mockSettingsDir() as userDir:

            if userArgs is not None:
                with open(op.join(userDir, 'default_arguments.txt'), 'wt') as f:
                    f.write(userArgs)

            if siteArgs is not None:
                with open(op.join(siteDir, 'default_arguments.txt'), 'wt') as f:
                    f.write(siteArgs)

            args    = fm.parseArgs([])
            expUser =  userArgs is not None
            expSite = (siteArgs is not None) and (userArgs is None)

            assert args.autoDisplay             == expUser
            assert args.neuroOrientation        == expUser
            assert args.notebook                == expSite
            assert args.hideOrientationWarnings == expSite
