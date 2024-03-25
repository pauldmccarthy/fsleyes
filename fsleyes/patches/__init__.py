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
    submods = sorted(m[1] for m in submods)

    for submod in  submods:
        log.debug('Applying patch: %s', submod)
        importlib.import_module(submod)
