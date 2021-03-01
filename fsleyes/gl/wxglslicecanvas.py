#!/usr/bin/env python
#
# wxglslicecanvas.py - The WXGLSliceCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLSliceCanvas` class, which is a
:class:`.SliceCanvas` for use in a :mod:`wx` application.
"""


import six

import wx
import wx.glcanvas as wxgl

import fsleyes_widgets as     fwidgets
import fsleyes_props   as     props

import fsleyes.gl      as     fslgl
from   .               import slicecanvas


class WXGLSliceCanvas(six.with_metaclass(fslgl.WXGLMetaClass,
                                         slicecanvas.SliceCanvas,
                                         fslgl.WXGLCanvasTarget,
                                         wxgl.GLCanvas)):
    """The ``WXGLSliceCanvas`` is a :class:`.SliceCanvas`, a
    :class:`wx.glcanvas.GLCanvas` and a :class:`.WXGLCanvasTarget`. If you
    want to use a :class:`.SliceCanvas` in your :mod:`wx` application, then
    you should use a ``WXGLSliceCanvas``.

    .. note:: The ``WXGLSliceCanvas`` assumes the existence of the
              :meth:`.SliceCanvas._updateDisplayBounds` method.
    """

    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Create a ``WXGLSliceCanvas``. See :meth:`.SliceCanvas.__init__` for
        details on the arguments.
        """

        attrs = fslgl.WXGLCanvasTarget.displayAttribues()

        wxgl.GLCanvas          .__init__(self, parent, **attrs)
        fslgl.WXGLCanvasTarget .__init__(self)
        slicecanvas.SliceCanvas.__init__(self, overlayList, displayCtx, zax)

        self.Bind(wx.EVT_SIZE, self.__onResize)


    def destroy(self):
        """Must be called when this ``WXGLSliceCanvas`` is no longer needed.
        Clears some event listeners and calls the base class ``destroy``
        method.
        """
        self.Unbind(wx.EVT_SIZE)
        slicecanvas.SliceCanvas.destroy(self)
        fslgl.WXGLCanvasTarget .destroy(self)


    def __onResize(self, ev):
        """Called on ``wx.EVT_SIZE`` events, when the canvas is resized. When
        the canvas is resized, we have to update the display bounds to preserve
        the aspect ratio.
        """
        ev.Skip()

        with props.skip(self.opts, 'displayBounds', self.name):
            centre = self.getDisplayCentre()
            self._updateDisplayBounds()
            self.centreDisplayAt(*centre)


    def Show(self, show):
        """Overrides ``GLCanvas.Show``. When running over SSH/X11, it doesn't
        seem to be possible to hide a ``GLCanvas`` - the most recent scene
        displayed on the canvas seems to persist, does not get overridden, and
        gets drawn on top of other things in the interface:

        .. image:: images/x11_slicecanvas_show_bug.png
           :scale: 50%
           :align: center

        This is not ideal, and I have no idea why it occurs. The only
        workaround that I've found to work is, instead of hiding the canvas,
        to set its size to 0. So this method does just that.
        """

        # If not in SSH, we can just
        # show/hide normally.
        if not fwidgets.inSSHSession():
            wxgl.GLCanvas.Show(self, show)

        elif not show:
            self.SetMinSize((0, 0))
            self.SetMaxSize((0, 0))
            self.SetSize(   (0, 0))


    def Hide(self):
        """Overrides ``GLCanvas.Hide``. Calls :meth:`Show`. """
        self.Show(False)
