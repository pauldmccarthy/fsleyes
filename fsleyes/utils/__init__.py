#!/usr/bin/env python
#
# __init__.py - Miscellaneous utility functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`fsleyes.utils` package contains miscellaneous utility functions
used throughout FSLeyes.
"""

import string


def makeValidMapKey(name):
    """Turns the given string into a valid key for use as a file-based
    identifier.
    """

    valid = string.ascii_lowercase + string.digits + '_-'
    key   = name.lower().replace(' ', '_')
    key   = ''.join([c for c in key if c in valid])

    return key


def isValidMapKey(key):
    """Returns ``True`` if the given string is a valid key for use as a
    file-based identifier, ``False`` otherwise. A valid key comprises lower
    case letters, numbers, underscores and hyphens.
    """

    valid = string.ascii_lowercase + string.digits + '_-'
    return all(c in valid for c in key)
