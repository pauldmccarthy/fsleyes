#!/usr/bin/env python
#
# cliserver.py - Infrastructure to call an existing FSLeyes instance from the
#                command line.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module implements a simple client-server architecture which can be
used to call an existing FSLeyes instance from the command line.


When FSLeyes is started with the ``--cliserver`` option, the :func:`runserver`
function is called to start a server thread. On subsequent invocations of
FSLeyes (with the ``--cliserver`` option), instead of starting up a new
FSLeyes instance, the command-line arguments are passed to the original
instance via the :func:`send` function.
"""


import os
import sys
import shlex
import atexit
import socket
import logging
import argparse
import threading

import fsl.utils.settings as fslsettings


log = logging.getLogger(__name__)


class CLIServerAction(argparse.Action):
    """Custom ``argparse.Action`` for applying the ``--cliserver`` command-line
    option.

    If a server is not running, the ``namespace.cliserver`` attribute is set
    to ``True``. Otherwise, the remaining arguments are passed to the
    :func:`send` function, and the process is closed via ``sys.exit``.

    In the former case (a server is not already running), the
    :mod:`fsleyes.main` module will start a server via :func:`runserver` at
    a later point in time.
    """

    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 0
        argparse.Action.__init__(self, *args, **kwargs)


    def __call__(self, parser, namespace, values, option_string):
        if not isRunning():
            setattr(namespace, self.dest, True)
            return
        else:
            # first arg is the current working
            # directory - see runserver
            argv = sys.argv[1:]
            argv.remove(option_string)
            argv = [os.getcwd()] + argv
            line = ' '.join(shlex.quote(a) for a in argv)
            send(line)
            sys.exit(0)


class AlreadyRunningError(Exception):
    """Raised by :func:`runserver` if a server loop is already running. """
    pass


class NotRunningError(Exception):
    """Raised by :func:`send` if a server loop is not running. """
    pass


def runserver(overlayList, displayCtx):
    """Starts a thread which runs the :func:`_serverloop` function.

    If a server is already running, within this or any other FSLeyes instance,
    an :exc:`AlreadyRunningError` is raised.

    Every line that is received is assumed to contain command line
    arguments specifying overlays to be loaded; these are passed
    to the :func:`.applyCommandLineArgs` function.

    :arg overlayList: The :class:`OverlayList`
    :arg displayCtx:  The master :class:`DisplayContext`
    """

    if isRunning():
        raise AlreadyRunningError()

    def callback(line):

        # first arg is the directory that
        # the client was executed from,
        # which is used by applyCLIArgs
        # in case overlays were specified
        # with relative paths
        args    = shlex.split(line)
        baseDir = args[0]
        args    = args[1:]

        import fsleyes.actions.applycommandline as applycli
        applycli.applyCommandLineArgs(overlayList,
                                      displayCtx,
                                      args,
                                      baseDir=baseDir)

    t        = threading.Thread(target=_serverloop, args=(callback,))
    t.daemon = True

    t.start()


def isRunning():
    """Returns ``True`` if (it looks like) a server is running, ``False``
    otherwise.
    """
    return fslsettings.readFile('cliserver.txt') is not None


def _serverloop(callback):
    """Starts a TCP server which runs forever.

    The server port number is written to the FSLeyes settings directoy in a
    file called ``cliserver.txt`` (see :mod:`fsl.utils.settings`).  Then,
    every line of text received on the socket is passed to the ``callback``
    function.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    sock.listen(1)
    port = sock.getsockname()[1]

    with fslsettings.writeFile('cliserver.txt') as f:
        f.write('{}'.format(port))

    atexit.register(fslsettings.deleteFile, 'cliserver.txt')

    log.debug('CLI server running on port %i', port)

    while True:
        conn, addr = sock.accept()

        log.debug('Connection from %s', addr)

        with conn:

            line = conn.makefile().readline().strip()

            log.debug('Received %s ...', line[:50])

            try:
                callback(line)
            except Exception as e:
                log.warning('Callback function raised error: %s',
                            e, exc_info=True)


def send(line):
    """If a cli server is running (see :func:`runserver` and
    :func:`_serverloop`), the given ``args`` are sent to it.

    A :exc:`NotRunningError` is raised if a server loop is not running.
    """

    if not isRunning():
        raise NotRunningError()

    with fslsettings.use(fslsettings.Settings('fsleyes', writeOnExit=False)):
        port = int(fslsettings.readFile('cliserver.txt').strip())

    line = (line + '\n').encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', port))

    log.debug('Sending to port %i: %s...', port, line[:50])

    sock.sendall(line)
