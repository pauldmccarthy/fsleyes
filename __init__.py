#!/usr/bin/env python
#
# __init__.py - FSLEyes - a python based OpenGL image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

"""A 3D image viewer.

The application logic is spread across several sub-packages:

 - :mod:`actions`        - Global actions (e.g. load file), and abstract base
                           classes for other actions, and entities which 
                           provide actions.

 - :mod:`controls`       - GUI panels which provide an interface to control 
                           the display of a single view.

 - :mod:`displaycontext` - Classes which define options controlling the
                           display.

 - :mod:`editor`         - Image editing functionality.

 - :mod:`gl`             - OpenGL visualisation logic.

 - :mod:`profiles`       - Mouse/keyboard interaction profiles.

 - :mod:`views`          - GUI panels which display image data.

 - :mod:`widgets`        - General purpose custom :mod:`wx` widgets.


A :class:`FSLEyesFrame` is a container for one or more 'views' - all of the
possible views are contained within the :mod:`.views` sub-package, and the
views which may be opened by the user are defined by the
:func:`.views.listViewPanels` function. View panels may contain one or more
'control' panels (all defined in the :mod:`.controls` sub-package), which
provide an interface allowing the user to control the view.


All view (and control) panels are derived from the :class:`.FSLEyesPanel`
which, in turn, is derived from the :class:`.ActionProvider` class.
As such, view panels may expose both actions, and properties, which can be
performed or modified by the user.
"""
