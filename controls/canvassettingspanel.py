#!/usr/bin/env python
#
# canvassettingspanel.py - The CanvasSettingsPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasSettingsPanel` class, a *FSLeyes
control* panel which displays settings for a :class:`.CanvasPanel`.
"""


import wx

import props

import pwidgets.widgetlist  as widgetlist

import fsl.data.strings     as strings
import fsl.fsleyes.panel    as fslpanel
import fsl.fsleyes.tooltips as fsltooltips


class CanvasSettingsPanel(fslpanel.FSLEyesPanel):
    """The ``CanvasSettingsPanel`` is a *FSLeyes control* which displays
    settings for a :class:`.CanvasPanel` instance. A ``CanvasSettingsPanel``
    looks something like this:

    .. image:: images/canvassettingspanel.png
       :scale: 50%
       :align: center


    The ``CanvasSettingsPanel`` displays controls which modify properties on
    the following classes:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.views.CanvasPanel
       ~fsl.fsleyes.displaycontext.SceneOpts
       ~fsl.fsleyes.displaycontext.OrthoOpts
       ~fsl.fsleyes.displaycontext.LightBoxOpts

    The ``CanvasSettingsPanel`` divides the displayed settings into those
    which are common to all :class:`.CanvasPanel` instances, and those which
    are specific to the :class:`.CanvasPanel` sub-class (i.e.
    :class:`.OrthoPanel` or :class:`.LightBoxPanel`).  The specific settings
    that are displayed are defined in the following lists:

    .. autosummary::

       _CANVASPANEL_PROPS
       _SCENEOPTS_PROPS
       _ORTHOOPTS_PROPS
       _LIGHTBOXOPTS_PROPS
    """

    
    def __init__(self, parent, overlayList, displayCtx, canvasPanel):
        """Create a ``CanvasSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        import fsl.fsleyes.views.orthopanel    as orthopanel
        import fsl.fsleyes.views.lightboxpanel as lightboxpanel

        if isinstance(canvasPanel, orthopanel.OrthoPanel):
            panelGroup = 'ortho'
            panelProps = _ORTHOOPTS_PROPS
            
        elif isinstance(canvasPanel, lightboxpanel.LightBoxPanel):
            panelGroup = 'lightbox'
            panelProps = _LIGHTBOXOPTS_PROPS

        self.__widgets.AddGroup('scene' ,    strings.labels[self, 'scene'])
        self.__widgets.AddGroup( panelGroup, strings.labels[self,  panelGroup])

        for dispProp in _CANVASPANEL_PROPS:

            widget = props.buildGUI(self.__widgets,
                                    canvasPanel,
                                    dispProp,
                                    showUnlink=False)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[canvasPanel, dispProp.key],
                tooltip=fsltooltips.properties[canvasPanel, dispProp.key],
                groupName='scene')

        opts = canvasPanel.getSceneOptions()

        for dispProp in _SCENEOPTS_PROPS:

            widget = props.buildGUI(self.__widgets,
                                    opts,
                                    dispProp,
                                    showUnlink=False)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, dispProp.key],
                tooltip=fsltooltips.properties[opts, dispProp.key],
                groupName='scene') 

        for dispProp in panelProps:

            widget = props.buildGUI(self.__widgets,
                                    opts,
                                    dispProp,
                                    showUnlink=False)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, dispProp.key],
                tooltip=fsltooltips.properties[opts, dispProp.key],
                groupName=panelGroup)

        self.__widgets.Expand('scene')
        self.__widgets.Expand(panelGroup)

        self.SetMinSize((21, 21))


_CANVASPANEL_PROPS = [
    props.Widget('syncOverlayOrder'),
    props.Widget('syncLocation'),
    props.Widget('syncOverlayDisplay'),
    props.Widget('movieMode'),
    props.Widget('movieRate', spin=False, showLimits=False),
]
"""A list of :class:`props.Widget` items defining controls to
display for :class:`.CanvasPanel` properties.
"""


_SCENEOPTS_PROPS = [
    props.Widget('showCursor'),
    props.Widget('bgColour'),
    props.Widget('cursorColour'),
    props.Widget('performance',
                 spin=False,
                 showLimits=False,
                 labels=strings.choices['SceneOpts.performance']),
    props.Widget('showColourBar'),
    props.Widget('colourBarLabelSide',
                 labels=strings.choices['SceneOpts.colourBarLabelSide'],
                 enabledWhen=lambda o: o.showColourBar),
    props.Widget('colourBarLocation',
                 labels=strings.choices['SceneOpts.colourBarLocation'],
                 enabledWhen=lambda o: o.showColourBar)
]
"""A list of :class:`props.Widget` items defining controls to
display for :class:`.SceneOpts` properties.
"""


_ORTHOOPTS_PROPS = [
    props.Widget('layout', labels=strings.choices['OrthoOpts.layout']), 
    props.Widget('zoom', spin=False, showLimits=False),
    props.Widget('showLabels'),
    props.Widget('showXCanvas'),
    props.Widget('showYCanvas'),
    props.Widget('showZCanvas')
]
"""A list of :class:`props.Widget` items defining controls to
display for :class:`.OrthoOpts` properties.
"""


_LIGHTBOXOPTS_PROPS = [
    props.Widget('zax', labels=strings.choices['CanvasOpts.zax']),
    props.Widget('zoom',         showLimits=False, spin=False),
    props.Widget('sliceSpacing', showLimits=False),
    props.Widget('zrange',       showLimits=False),
    props.Widget('highlightSlice'),
    props.Widget('showGridLines') 
]
"""A list of :class:`props.Widget` items defining controls to
display for :class:`.LightBoxOpts` properties.
"""
