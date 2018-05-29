#!/usr/bin/env python
#
# colourbar.py - The ColourBarPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarPanel`, a :class:`.FSLeyesPanel`
which renders a colour bar.
"""


import wx

import fsleyes.panel                  as fslpanel
import fsleyes.gl.wxglcolourbarcanvas as cbarcanvas


class ColourBarPanel(fslpanel.FSLeyesPanel):
    """The ``ColourBarPanel`` is a panel which shows a colour bar, depicting
    the data range of the currently selected overlay (if applicable). A
    :class:`.ColourBarCanvas` is used to render the colour bar.


    .. note:: Currently, the ``ColourBarPanel`` will only display a colour bar
              for overlays which are associated with a :class:`.ColourMapOpts`
              instance.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``ColourBarPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__cbCanvas = cbarcanvas.WXGLColourBarCanvas(
            self, overlayList, displayCtx)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__cbCanvas, flag=wx.EXPAND, proportion=1)

        self.__cbCanvas.colourBar.addListener(
            'orientation', self.name, self.__layout)
        self.__layout()


    def getCanvas(self):
        """Returns the :class:`.ColourBarCanvas` which displays the rendered
        colour bar.
        """
        return self.__cbCanvas


    @property
    def canvas(self):
        """Returns the :class:`.ColourBarCanvas` which displays the rendered
        colour bar.
        """
        return self.__cbCanvas


    @property
    def colourBar(self):
        """Returns the :class:`.ColourBar` which generates the colour bar
        bitmap.
        """
        return self.__cbCanvas.colourBar


    def destroy(self):
        """Must be called when this ``ColourBarPanel`` is no longer needed. """

        self.__cbCanvas.colourBar.removeListener('orientation', self.name)
        self.__cbCanvas.destroy()
        self.__cbCanvas = None

        fslpanel.FSLeyesPanel.destroy(self)


    def __layout(self, *a):
        """Called when this ``ColourBarPanel`` needs to be laid out.
        Sets the panel size, and calls the :meth:`__refreshColourBar` method.
        """

        # Fix the minor axis of the colour bar to 75 pixels
        if self.__cbCanvas.colourBar.orientation == 'horizontal':
            self.__cbCanvas.SetSizeHints(-1, 60, -1, 60, -1, -1)
        else:
            self.__cbCanvas.SetSizeHints(60, -1, 60, -1, -1, -1)

        self.Layout()
