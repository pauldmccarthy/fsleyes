#!/usr/bin/env python
#
# displayspacewarning.py - The DisplaySpaceWarning class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`DisplaySpaceWarning`, a FSLeyes
control widget which displays a warning when the
:attr:`.DisplayContext.displaySpace` has a value which is preventing
the user from seeing or doing something.
"""


import                   logging
import                   wx
import wx.lib.agw.aui as wxaui

import fsl.utils.idle  as idle
import fsleyes.panel   as fslpanel
import fsleyes.strings as strings


log = logging.getLogger(__name__)


class DisplaySpaceWarning(fslpanel.FSLeyesPanel):
    """The ``DisplaySpaceWarning`` is a panel which contains a message and a
    button. When the :attr:`.DisplayContext.displaySpace` is set to a value
    that matches the ``warnCondition`` passed to ``__init__``, the warning
    message and button are shown, otherwise the entire panel is hidden. When
    the user pushes the button, the ``displaySpace`` is changed to the value
    specified by ``changeTo``.
    """

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 frame,
                 msg,
                 warnCondition,
                 changeTo):
        """Create a ``DisplaySpaceWarning``.

        :arg parent:        ``wx`` parent object
        :arg overlayList:   The :class:`.OverlayList`
        :arg displayCtx:    The :class:`.DisplayContext`
        :arg frame:         The :class:`.FSLeyesFrame`

        :arg msg:           Message to display

        :arg warnCondition: One of ``'world'``, ``'overlay'``,
                            ``'not overlay'``, or ``'not like overlay'``

        :arg changeTo:      One of ``'world'`` or ``'overlay'``
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__warnCondition = warnCondition
        self.__changeTo      = changeTo
        self.__dsWarning     = wx.StaticText(self)
        self.__changeDS      = wx.Button(    self)

        self.__dsWarning.SetLabel(msg)
        self.__changeDS .SetLabel(strings.labels[self, 'changeDS'])

        self.__dsWarning.SetForegroundColour((192, 0, 0, 255))

        self.__sizer     = wx.BoxSizer(wx.HORIZONTAL)
        self.__realSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__realSizer.Add((1, 1),           flag=wx.EXPAND)
        self.__realSizer.Add(self.__dsWarning)
        self.__realSizer.Add((10, 1))
        self.__realSizer.Add(self.__changeDS,  flag=wx.ALIGN_CENTRE_VERTICAL)
        self.__realSizer.Add((1, 1),           flag=wx.EXPAND)
        self.__sizer    .Add(self.__realSizer, flag=wx.EXPAND)

        self.SetSizer(self.__sizer)

        self.__changeDS .Bind(wx.EVT_BUTTON, self.__onChangeDS)

        displayCtx .addListener('displaySpace',
                                self.name,
                                self.__displaySpaceChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__displaySpaceChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__displaySpaceChanged)

        idle.idle(self.__displaySpaceChanged)


    def destroy(self):
        """Must be called when this ``DisplaySpaceWarning`` is no longer
        needed. De-registers listeners.
        """

        displayCtx  = self.displayCtx
        overlayList = self.overlayList

        displayCtx .removeListener('displaySpace',    self.name)
        displayCtx .removeListener('selectedOverlay', self.name)
        overlayList.removeListener('overlays',        self.name)

        fslpanel.FSLeyesPanel.destroy(self)


    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` property
        changes. If it has been given a setting that would cause the
        transformation changes to have no effect on the display, a warning
        message is shown.
        """

        parent       = self.GetParent()
        condition    = self.__warnCondition
        displayCtx   = self.displayCtx
        displaySpace = displayCtx.displaySpace
        overlay      = displayCtx.getSelectedOverlay()

        if   condition == 'overlay':     show = displaySpace is overlay
        elif condition == 'not overlay': show = displaySpace is not overlay
        elif condition == 'world':       show = displaySpace == 'world'
        elif condition == 'like overlay':
            if displaySpace == 'world':
                show = False
            else:
                show = overlay.sameSpace(displaySpace)
        elif condition == 'not like overlay':
            if displaySpace == 'world':
                show = True
            else:
                show = not overlay.sameSpace(displaySpace)
        else:
            show = False

        if show:
            log.debug('Showing display space warning ({} / {})'.format(
                displaySpace, condition))

        self.__sizer.Show(self.__realSizer, show)
        self.Layout()
        self.Fit()

        sizer = parent.GetSizer()
        parent.SetInitialSize(sizer.GetMinSize())

        parent = parent.GetTopLevelParent()
        sizer  = parent.GetSizer()
        if isinstance(parent, wxaui.AuiFloatingFrame):
            parent.SetInitialSize(sizer.GetMinSize())
            parent.Layout()
            parent.Fit()


    def __onChangeDS(self, ev):
        """Called when the *Change display space* button is pushed. This button
        is only shown if the :attr:`.DisplayContext.displaySpace` is set to
        something which causes the transformation change to have no effect on
        the display. This method changes the ``displaySpace`` to that
        specified by the ``changeTo`` argument passed to :meth:`__init__`.
        """

        changeTo   = self.__changeTo
        displayCtx = self.displayCtx

        if changeTo == 'world':
            newSpace = 'world'
        elif changeTo == 'overlay' and len(self.overlayList) > 0:
            newSpace = displayCtx.getSelectedOverlay()
            newSpace = displayCtx.getReferenceImage(newSpace)

        log.debug('Changing displaySpace to {}'.format(newSpace))
        displayCtx.displaySpace = newSpace
