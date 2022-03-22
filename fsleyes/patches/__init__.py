#!/usr/bin/env python


import sys
import logging
import pkgutil
import importlib


log = logging.getLogger(__name__)


def apply():

    mod     = sys.modules[__name__]
    path    = mod.__path__
    name    = mod.__name__
    submods = pkgutil.iter_modules(path, f'{name}.')

    for subpath, subname, _ in  submods:
        log.debug('Applying patch: %s', subname)
        importlib.import_module(subname)
