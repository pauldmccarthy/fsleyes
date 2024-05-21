#!/usr/bin/env python
#
# lazyimporter.py - Mechanism to lazily import a module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`lazyimport` function, which can be used to
lazily import a Python module. The module not imported until an attempt is
made to access its contents.
"""


import importlib


class LazyImporter:
    """Class which lazily imports a module. Acts as a proxy for the module,
    and imports it on the first attempt to access an attribute.
    """


    def __init__(self, name, ref=None):
        """Create a ``LazyImporter`` for the module called ``name``.

        If ``ref`` is provided, it is expected to be the full reference to a
        module-level attribute.  When the module is imported, the reference is
        replaced with the module.

        :arg name: Module to lazily import
        :arg ref:  Reference to replace with the module when it is imported
        """
        self.__name   = name
        self.__ref    = ref
        self.__module = None


    def __getattr__(self, field):
        """Imports the module and returns the requested attribute. """
        self.ensureImported()
        return getattr(self.__module, field)


    @property
    def hasBeenImported(self):
        """Returns ``True`` if the module has been imported, ``False``
        otherwise.
        """
        return self.__module is not None


    def ensureImported(self):
        """Called by :meth:`__getattr__`. Imports the module and, if a ``ref``
        was provided, replaces that reference with the imported module.
        """

        if self.__module is not None:
            return

        self.__module = importlib.import_module(self.__name)

        if self.__ref is not None:
            refmod, refname = self.__ref.rsplit('.', 1)
            refmod          = importlib.import_module(refmod)
            setattr(refmod, refname, self.__module)


def lazyimport(name, ref=None):
    """Lazily import the module called ``name``.

    If ``ref`` is provided, it is expected to be the full reference to a
    module-level attribute.  When the module is imported, the reference is
    replaced with the module.

    :arg name: Module to lazily import
    :arg ref:  Reference to replace with the module when it is imported

    :return:   A :class:`LazyImporter` instance.
    """
    return LazyImporter(name, ref)
