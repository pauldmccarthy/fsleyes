#!/usr/bin/env python
#
# version.py - FSLeyes version information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The sole purpose of this module is as a container for the *FSLeyes*
version number.

The ``__version__`` field contains the current FSLeyes version number, as a
string.  The FSLeyes version number consists of three numbers, separated by a
period, which roughly obeys the Semantic Versioning conventions
(http://semver.org/).

The version number is automatically managed with ``setuptools-scm``.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fsleyes")
except PackageNotFoundError:
    __version__ = '<unknown>'
