#!/usr/bin/env python
#
# __init__.py - FSLeyes control panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``controls`` package is the home of all *FSLeyes controls*, as
described in the :mod:`~fsleyes` package documentation.


Every control panel is a sub-class of either the :class:`.FSLeyesPanel` or
:class:`.FSLeyesToolBar`, and each panel allows the user to control some
aspect of either the specific :class:`.ViewPanel` that the control panel is
embedded within, or some general aspect of *FSLeyes*.
"""
