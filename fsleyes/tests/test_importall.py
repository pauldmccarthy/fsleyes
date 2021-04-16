#!/usr/bin/env python
#
# test_importall.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pkgutil
import importlib
import fsleyes


def test_importall():

    def recurse(module):

        path    = module.__path__
        name    = module.__name__
        submods = list(pkgutil.iter_modules(path, '{}.'.format(name)))

        for i, (spath, smodname, ispkg) in enumerate(submods):

            submod = importlib.import_module(smodname)

            if ispkg:
                recurse(submod)

    recurse(fsleyes)
