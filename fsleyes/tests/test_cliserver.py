#!/usr/bin/env python
#
# test_cliserver.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import time
import argparse
import threading
import contextlib
import functools as ft

from unittest import mock

import pytest

import fsleyes.cliserver as cliserver

from six import StringIO


class MockSettings(object):


    @property
    def __file__(self):
        return 'Yo11!!!!'

    def __init__(self, *args, **kwargs):
        self.contents = {}

    def Settings(self, *args, **kwargs):
        return self

    def readFile(self, name):
        return self.contents.get(name, None)

    @contextlib.contextmanager
    def writeFile(self, name):
        strm = StringIO('')
        try:
            yield strm
        finally:
            strm.seek(0)
            self.contents[name] = strm.read()

    def deleteFile(self, name):
        self.contents.pop(name, None)

    @contextlib.contextmanager
    def use(self, *a, **kwa):
        yield



def test_server():

    received = [None]

    class MockApplyCLIArgs(object):
        def applyCommandLineArgs(self, ovlList, displayCtx, args, baseDir):
            received[0] = ' '.join([baseDir] + list(args))


    die  = threading.Event()
    acli = MockApplyCLIArgs()
    stgs = MockSettings()

    with mock.patch('fsleyes.cliserver.fslsettings', stgs), \
         mock.patch('fsleyes.cliserver.applycli',    acli):

        cliserver.runserver(None, None, ev=die)
        time.sleep(1)

        cliserver.send('Hey 1 2 3')
        time.sleep(1)
        die.set()

    assert received[0] == 'Hey 1 2 3'


def test_CliServerAction():

    sent = [None]
    def mockSend(line):
        sent[0] = line

    isRunningVal = False
    def mockIsRunning():
        return isRunningVal

    # client side
    with mock.patch('fsleyes.cliserver.send',      mockSend), \
         mock.patch('fsleyes.cliserver.isRunning', mockIsRunning):

        args = '--server -a -b -c d'.split()

        srvact = ft.partial(cliserver.CLIServerAction,
                            allArgs=args)

        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-s', '--server',
            action=srvact)

        ns = parser.parse_args(['--server'])

        # server side
        assert ns.server
        assert sent[0] is None

        isRunningVal = True
        with pytest.raises(SystemExit):
            parser.parse_known_args(args)
        cwd = os.getcwd()
        assert sent[0]  == ' '.join([cwd] + args[1:])
