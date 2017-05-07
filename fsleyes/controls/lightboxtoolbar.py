#!/usr/bin/env python
#
# lightboxtoolbar.py - The LightBoxToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxToolBar` class, which is a
:class:`.FSLeyesToolBar` for use with the :class:`.LightBoxPanel`.
"""


import wx

import fsleyes_props    as props

import fsleyes.toolbar  as fsltoolbar
import fsleyes.actions  as actions
import fsleyes.icons    as fslicons
import fsleyes.tooltips as fsltooltips
import fsleyes.strings  as strings


BUM_MODE = False
"""If ``True``, the icon used for the coronal toggle button is made to look
like a bum.
"""


class LightBoxToolBar(fsltoolbar.FSLeyesToolBar):
    """The ``LightBoxToolBar`` is a :class:`.FSLeyesToolBar` for use with the
    :class:`.LightBoxPanel`. A ``LightBoxToolBar`` looks something like this:


    .. image:: images/lightboxtoolbar.png
       :scale: 50%
       :align: center


    The ``LightBoxToolBar`` allows the user to control important parts of the
    :class:`.LightBoxPanel` display, and also to display a
    :class:`.CanvasSettingsPanel`, which allows control over all aspects of a
    ``LightBoxPanel``.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, lb):
        """Create a ``LightBoxToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg lb:          The :class:`.LightBoxPanel` instance.
        """

        fsltoolbar.FSLeyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           frame,
                                           height=24,
                                           kbFocus=True)

        self.lightBoxPanel = lb

        lbOpts = lb.getSceneOptions()

        if BUM_MODE: coronalIcon          = 'coronalBumSlice24'
        else:        coronalIcon          = 'coronalSlice24'
        if BUM_MODE: coronalHighlightIcon = 'coronalBumSliceHighlight24'
        else:        coronalHighlightIcon = 'coronalSliceHighlight24'

        icons = {
            'screenshot'                : fslicons.findImageFile('camera24'),
            'movieMode'                 : [
                fslicons.findImageFile('movieHighlight24'),
                fslicons.findImageFile('movie24')],
            'toggleCanvasSettingsPanel' : [
                fslicons.findImageFile('spannerHighlight24'),
                fslicons.findImageFile('spanner24')],

            'zax' : {
                0 : [fslicons.findImageFile('sagittalSliceHighlight24'),
                     fslicons.findImageFile('sagittalSlice24')],
                1 : [fslicons.findImageFile(coronalHighlightIcon),
                     fslicons.findImageFile(coronalIcon)],
                2 : [fslicons.findImageFile('axialSliceHighlight24'),
                     fslicons.findImageFile('axialSlice24')],
            }
        }

        tooltips = {

            'screenshot'   : fsltooltips.actions[   lb,      'screenshot'],
            'movieMode'    : fsltooltips.properties[lb,      'movieMode'],
            'zax'          : fsltooltips.properties[lbOpts,  'zax'],
            'sliceSpacing' : fsltooltips.properties[lbOpts,  'sliceSpacing'],
            'zrange'       : fsltooltips.properties[lbOpts,  'zrange'],
            'zoom'         : fsltooltips.properties[lbOpts,  'zoom'],
            'toggleCanvasSettingsPanel' : fsltooltips.actions[
                lb, 'toggleCanvasSettingsPanel'],
        }

        specs = {

            'toggleCanvasSettingsPanel' : actions.ToggleActionButton(
                'toggleCanvasSettingsPanel',
                actionKwargs={'floatPane' : True},
                icon=icons['toggleCanvasSettingsPanel'],
                tooltip=tooltips['toggleCanvasSettingsPanel']),

            'screenshot' : actions.ActionButton(
                'screenshot',
                icon=icons['screenshot'],
                tooltip=tooltips['screenshot']),

            'movieMode'    : props.Widget(
                'movieMode',
                icon=icons['movieMode'],
                tooltip=tooltips['movieMode']),

            'zax'          : props.Widget(
                'zax',
                icons=icons['zax'],
                tooltip=tooltips['zax']),

            'sliceSpacing' : props.Widget(
                'sliceSpacing',
                spin=False,
                showLimits=False,
                tooltip=tooltips['sliceSpacing']),

            'zrange'       : props.Widget(
                'zrange',
                spin=False,
                showLimits=False,
                tooltip=tooltips['zrange'],
                labels=[strings.choices[lbOpts, 'zrange', 'min'],
                        strings.choices[lbOpts, 'zrange', 'max']]),

            'zoom'         : props.Widget(
                'zoom',
                spin=False,
                showLimits=False,
                tooltip=tooltips['zoom']),
        }

        # Slice spacing and zoom go on a single panel
        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(2, 2, 0, 0)
        panel.SetSizer(sizer)

        more         = props.buildGUI(self,
                                      lb,
                                      specs['toggleCanvasSettingsPanel'])
        screenshot   = props.buildGUI(self,  lb,         specs['screenshot'])
        movieMode    = props.buildGUI(self,  lb,         specs['movieMode'])
        zax          = props.buildGUI(self,  lbOpts,     specs['zax'])
        zrange       = props.buildGUI(self,  lbOpts,     specs['zrange'])
        zoom         = props.buildGUI(panel, lbOpts,     specs['zoom'])
        spacing      = props.buildGUI(panel, lbOpts,     specs['sliceSpacing'])
        zoomLabel    = wx.StaticText(panel)
        spacingLabel = wx.StaticText(panel)

        zoomLabel   .SetLabel(strings.properties[lbOpts, 'zoom'])
        spacingLabel.SetLabel(strings.properties[lbOpts, 'sliceSpacing'])

        sizer.Add(zoomLabel)
        sizer.Add(zoom,    flag=wx.EXPAND)
        sizer.Add(spacingLabel)
        sizer.Add(spacing, flag=wx.EXPAND)

        tools = [more,
                 screenshot,
                 fsltoolbar.ToolBarDivider(self,
                                           height=24,
                                           orient=wx.VERTICAL),
                 zax,
                 fsltoolbar.ToolBarDivider(self,
                                           height=24,
                                           orient=wx.VERTICAL),
                 movieMode,
                 zrange,
                 panel]
        nav   = [more, screenshot, zax, movieMode, zrange, zoom, spacing]

        self.SetTools(tools)
        self.setNavOrder(nav)
