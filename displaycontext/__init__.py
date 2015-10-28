#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``displaycontext`` package contains classes which define the display
options for pretty much everything in *FSLeyes*.  


.. note:: Before perusing this package, you should read the high level
          overview in the :mod:`~fsl.fsleyes` package documentation. Go on -
          it won't take you too long.


--------
Overview
--------


The most important classes defined in this package are:

  - the :class:`.DisplayContext` class, which defines how all of the
    overlays in an :class:`.OverlayList` should be displayed.

  - the :class:`.Display` class, which defines how a single overlay should be
    displayed.

  - the :class:`.DisplayOpts` base class, and its sub-classes, which define
    overlay type specific options.


A :class:`.DisplayContext` instance encapsulates an :class:`.OverlayList`, and
defines how the overlays in the list should be displayed.  Each
:class:`.ViewPanel` displayed in *FSLeyes* (e.g. the :class:`.OrthoPanel`) has
its own ``DisplayContext`` instance; a ``ViewPanel`` uses its
``DisplayContext`` instance to configure general display properties, and also
to access the :class:`.Display` properties for individual overlays.


All of the classes mentioned on ths page are defined in sub-modules, but are
imported into, and are thus available from, the ``displaycontext`` package
namespace. For example::

    import fsl.fsleyes.displaycontext as fsldc

    # The VolumeOpts class is defined in the
    # fsl.fsleyes.displaycontext.volumeopts
    # module, but is available in the 
    # fsl.fsleyes.displaycontext namespace.
    volopts = fsldc.VolumeOpts(overlay, display, overlayList, displayCtx)


-----------------------
Overlay display options
-----------------------


The :class:`.Display` class, and the :class:`.DisplayOpts` sub-classes define
how to display a single overlay. Options common to all overlays
(e.g. :attr:`.Display.brightness`, :attr:`.Display.alpha`) are defined in the
``Display`` class, whereas options which are specific to a particular overlay
type (e.g. :attr:`.VolumeOpts.cmap`, :attr:`.LineVectorOpts.lineWidth`) are
defined in the corresponding :class:`.DisplayOpts` sub-class.


The ``Display`` instance for a particular overlay owns and manages a single
``DisplayOpts`` instance - whenever the overlay display type is changed, the
``Display`` instance deletes the old ``DisplayOpts`` instance, and creates a
new one accordingly.  The following ``DisplayOpts`` sub-classes exist:

.. autosummary::
   :nosignatures:

   ~fsl.fsleyes.displaycontext.volumeopts.ImageOpts
   ~fsl.fsleyes.displaycontext.volumeopts.VolumeOpts
   ~fsl.fsleyes.displaycontext.maskopts.MaskOpts
   ~fsl.fsleyes.displaycontext.vectoropts.VectorOpts
   ~fsl.fsleyes.displaycontext.vectoropts.RGBVectorOpts
   ~fsl.fsleyes.displaycontext.vectoropts.LineVectorOpts
   ~fsl.fsleyes.displaycontext.modelopts.ModelOpts
   ~fsl.fsleyes.displaycontext.labelopts.LabelOpts


--------------
Overlay groups
--------------


.. note:: Support for overlay groups is quite basic at this point in time. See
          the :class:`.OverlayListPanel` for details.

The :mod:`~.displaycontext.group` module provides the functionality to
link the display properties of one or more overlays. One or more
:class:`.OverlayGroup` instances may be added to the
:attr:`.DisplayContext.overlayGroups` list.


-------------
Scene options
-------------


Independent of the ``DisplayContext``, ``Display`` and ``DisplayOpts``
classes, the ``displaycontext`` package is also home to a few classes which
define *scene* options:


.. autosummary::
   :nosignatures:

   ~fsl.fsleyes.displaycontext.canvasopts.SliceCanvasOpts
   ~fsl.fsleyes.displaycontext.canvasopts.LightBoxCanvasOpts
   ~fsl.fsleyes.displaycontext.sceneopts.SceneOpts
   ~fsl.fsleyes.displaycontext.orthoopts.OrthoOpts
   ~fsl.fsleyes.displaycontext.lightboxopts.LightBoxOpts


.. note:: Aside from an increase in code modularity and cleanliness, another
          reason that all of these scene display settings are separated from
          the things that use them is so they can be imported, queried, and
          set without having to import the modules that use them.

          For example, the :mod:`.fsleyes_parseargs` module needs to be able
          to access all of the display settings in order to print out the
          corresponding help documentation. This process would take much
          longer if ``fsleyes_parseargs`` had to import, e.g.
          :class:`.OrthoPanel`, which would result in importing both :mod:`wx`
          and :mod:`.OpenGL`.

          Keeping these display settings separate allows us to avoid these
          time-consuming imports in situations where they are not needed.
"""


import display


from displaycontext import DisplayContext
from display        import Display
from group          import OverlayGroup
from sceneopts      import SceneOpts
from orthoopts      import OrthoOpts
from lightboxopts   import LightBoxOpts
from volumeopts     import ImageOpts
from volumeopts     import VolumeOpts
from maskopts       import MaskOpts
from vectoropts     import VectorOpts
from vectoropts     import RGBVectorOpts
from vectoropts     import LineVectorOpts
from modelopts      import ModelOpts
from labelopts      import LabelOpts


from displaycontext import InvalidOverlayError


ALL_OVERLAY_TYPES = list(set(
    reduce(lambda a, b: a + b,
           display.OVERLAY_TYPES.values())))
"""This attribute contains a list of all possible overlay types - see the
:attr:`.Display.overlayType` property and tge :data:`.display.OVERLAY_TYPES`
dictionary for more details.
"""
