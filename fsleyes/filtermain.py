#!/usr/bin/env python
#
# filtermain.py - Wrapper around fsleyes.main
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides an alternate FSLeyes entry point to
(func:`fsleyes.main.main`).

The :func:`main` function in this module calls :func:`fsleyes.main.main`, but
additionally intercepts and filters the standard out/error streams, and drops
useless warnings/errors which originate from underlying libraries.
"""


import os
import re
import sys
import queue
import logging
import warnings
import threading


# Filters may be either:
#   - a regex string, or
#   - a tuple of (regex string, total number of lines to skip)

FILTERS = [
    r'Adding duplicate image handler',
    r'Value error parsing header in AFM',
    r'Metadata\.framework \[Error\]',
    r'Class FIFinderSyncExtensionHost',
    r'_RegisterApplication()',
    r'FinderKit',
    r'CoreText note: Client requested name',
    (r'DeprecationWarning', 2),
    r'wx.NewId',
    r'ioloop.install',
    r'FutureWarning',
    r'ShimWarning',
    r'ClientToScreen',
    r'ScreenToClient',
    r'Gdk-WARNING',
    (r'Gtk-WARNING', 2),
    r'Gtk-Message',
    (r'Gtk-CRITICAL', 2),
    r'Glib-CRITICAL',
    r'GLib-GObject-WARNING',
    r'libGL error',
    r'Pango-WARNING',
    r'Xlib:  extension',
    r'CRITICAL \*\*',
    r'No matching fbConfigs',
    r'failed to load driver: swrast',
    r'\*\*\* BUG \*\*\*',
    r'In pixman',
    r'Set a breakpoint',
]


def filter_stream(stream, die, filters=None):
    """Intercept the given output stream, and filter it according to the
    filters above. The filter is run on a separate thread.

    :arg stream:  File-like to read from and filter.

    :arg die:     ``threading.Event`` object - when it is set the filter
                  thread will end gracefully.

    :arg filters: List of regular expressions to filter. If ``None``, defaults
                  to :attr:`FILTERS`.
    """

    if filters is None:
        filters = FILTERS

    # I only loosely understand how to manipulate
    # file descriptors. Useful resources:
    #
    #  - https://linuxmeerkat.wordpress.com/2011/12/02/\
    #    file-descriptors-explained/
    #  - https://stackoverflow.com/a/24277852
    #  - https://stackoverflow.com/a/17954769
    #  - https://stackoverflow.com/a/10759061

    # Redirect the stream into a pipe,
    # and filter the pipe output
    fd           = stream.fileno()
    oldfd        = os.dup(fd)
    piper, pipew = os.pipe()
    os.dup2(pipew, fd)
    os.close(pipew)

    fin  = os.fdopen(piper, 'r')
    fout = os.fdopen(oldfd, 'w')

    # Use a queue to pass lines from
    # the input stream to the output
    # stream.
    q = queue.Queue()

    # Use a Barrier to synchronise the
    # read, write, and calling threads
    alive = threading.Barrier(3)

    # The read thread runs forever,
    # just putting lines in the queue.
    def read_loop():
        alive.wait()
        while True:
            line = fin.readline()
            if line == '':
                break
            q.put(line)


    def testline(line):
        for pat in filters:

            if isinstance(pat, tuple): pat, skip = pat
            else:                      skip      = 1

            if re.search(pat, line):
                return skip
        return 0

    # The write thread runs until both
    # of the following are true:
    #
    #  - there are no lines in the queue
    #  - the die event has been set
    def write_loop():
        skip = 0
        alive.wait()
        while True:
            try:
                line = q.get(timeout=0.25)
            except queue.Empty:
                if die.is_set(): break
                else:            continue

            if skip > 0:
                skip -= 1
                continue

            skip = testline(line) - 1

            if skip < 0:
                fout.write(line)
                fout.flush()

        # Restore the original stream
        try:
            os.close(fd)
            os.close(piper)
            os.dup2(oldfd, fd)
            os.close(oldfd)
        except Exception:
            pass

    rt = threading.Thread(target=read_loop,  daemon=True)
    wt = threading.Thread(target=write_loop, daemon=True)
    rt.start()
    wt.start()

    return rt, wt, alive


def main(args=None):
    """Alternate FSLeyes entry point.

    Uses the :func:`filter_stream` function to filter the standard
    output/error streams, then calls :func:`fsleyes.main.main`.
    """

    warnings.filterwarnings('ignore', module='matplotlib')
    warnings.filterwarnings('ignore', module='xnat')
    warnings.filterwarnings('ignore', module='mpl_toolkits')
    warnings.filterwarnings('ignore', module='numpy')
    warnings.filterwarnings('ignore', module='h5py')
    warnings.filterwarnings('ignore', module='notebook')
    warnings.filterwarnings('ignore', module='trimesh')
    warnings.filterwarnings('ignore', module='h5py')
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    logging.getLogger('nibabel')  .setLevel(logging.CRITICAL)
    logging.getLogger('trimesh')  .setLevel(logging.CRITICAL)
    logging.getLogger('traitlets').setLevel(logging.CRITICAL)

    die                        = threading.Event()
    rtstdout, wtstdout, oalive = filter_stream(sys.stdout, die)
    rtstderr, wtstderr, ealive = filter_stream(sys.stderr, die)

    import fsleyes.main as fm

    # wait until the filter
    # threads have started
    oalive.wait()
    ealive.wait()

    result = 1

    try:
        result = fm.main(args)
    except SystemExit as e:
        result = e.code
    finally:
        die.set()
        wtstderr.join()
        wtstdout.join()
        rtstdout.join()
        rtstderr.join()

    sys.exit(result)


if __name__ == '__main__':
    main()
