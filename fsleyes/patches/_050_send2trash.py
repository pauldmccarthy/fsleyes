#!/usr/bin/env python
#
# _050_send2trash.py - Completely overwite send2trash on old macOS versions
#                      to work around
#                      https://github.com/arsenetar/send2trash/issues/83
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging
import os
import platform
import sys


log = logging.getLogger(__name__)


class send2trash:

    @staticmethod
    def send2trash(paths):
        if isinstance(paths, (str, bytes)):
            paths = [paths]

        for path in paths:
            try:
                os.remove(path)
            except Exception as e:
                log.warning('Unable to remove path %s (%e)', path, e)

if platform.system().lower() == 'darwin':
    macos_ver = tuple(int(p) for p in platform.mac_ver()[0].split('.'))[:2]

    if macos_ver <= (10, 14):
        sys.modules['send2trash'] = send2trash
