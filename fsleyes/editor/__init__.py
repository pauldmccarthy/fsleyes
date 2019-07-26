#!/usr/bin/env python
#
# __init__.py - Editing of Image overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``editor`` package contains functionality for editing :class:`.Image`
overlays.

.. image:: images/editor.png
   :scale: 25%
   :align: center


The ``editor`` package provides the following two classes:

.. autosummary::
   :nosignatures:

   ~fsleyes.editor.selection.Selection
   ~fsleyes.editor.editor.Editor


Making an edit to an ``Image`` requires two stages:

 1. Select some voxels in the ``Image``.

 2. Modify the values stored in those voxels.


The :class:`.Selection` class implements the functionality for the first
stage, and the :class:`.Editor` class implements functinoality for the second.
The ``Editor`` class also keeps track of changes to the current selection, and
to the image data, thus allowing the user to undo/redo any changes.
"""


__all__ = ['isEditable',
           'Editor',
           'Selection',
           'ValueChange',
           'SelectionChange']


import fsl.data.image         as fslimage
import fsleyes.displaycontext as fsldisplay

from .selection import  Selection
from .editor    import (Editor,
                        ValueChange,
                        SelectionChange)


def isEditable(overlay, displayCtx):
    """Returns ``True`` if the given overlay is editable, ``False``
    otherwise.

    :arg overlay:    The overlay to check
    :arg displayCtx: The relevant :meth:`.DisplayContext`
    :returns:        True if ``overlay``is editable, ``False`` otherwise
    """

    # will raise if overlay is
    # None, or has been removed
    try:
        display = displayCtx.getDisplay(overlay)
    except (ValueError, fsldisplay.InvalidOverlayError):
        return False

    # Edit mode is only supported on
    # images with the 'volume', 'mask'
    # or 'label' types
    return overlay is not None                 and \
           isinstance(overlay, fslimage.Image) and \
           overlay.nvals == 1                  and \
           display.overlayType in ('volume', 'mask', 'label')
