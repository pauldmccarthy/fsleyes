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

import fsl.data.image       as fslimage
import fsl.fsleyes.panel    as fslpanel
import fsl.fsleyes.tooltips as fsltooltips
import fsl.fsleyes.strings  as strings



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
    :class:`.OrthoPanel` or :class:`.LightBoxPanel`).  
    """

    
    def __init__(self, parent, overlayList, displayCtx, canvasPanel):
        """Create a ``CanvasSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__canvasPanel = canvasPanel
        self.__widgets     = widgetlist.WidgetList(self)
        self.__sizer       = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        self.__makeTools()

        self.SetMinSize((21, 21))


    def __makeTools(self):

        displayCtx  = self._displayCtx
        canvasPanel = self.__canvasPanel

        canvasPanelProps = [
            props.Widget('syncOverlayOrder'),
            props.Widget('syncLocation'),
            props.Widget('syncOverlayDisplay'),
            props.Widget('movieMode'),
            props.Widget('movieRate', spin=False, showLimits=False)]

        sceneOptsProps = [
            props.Widget('showCursor'),
            props.Widget('bgColour'),
            props.Widget('cursorColour'),
            props.Widget('performance',
                         spin=False,
                         showLimits=False,
                         labels=strings.choices['SceneOpts.performance']),
            props.Widget('showColourBar'),
            props.Widget('colourBarLabelSide',
                         labels=strings.choices[
                             'SceneOpts.colourBarLabelSide'],
                         enabledWhen=lambda o: o.showColourBar),
            props.Widget('colourBarLocation',
                         labels=strings.choices['SceneOpts.colourBarLocation'],
                         enabledWhen=lambda o: o.showColourBar)]

        def _displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Nifti1):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]

        displayCtxProps = [
            props.Widget('displaySpace',
                         labels=_displaySpaceOptionName,
                         dependencies=[(canvasPanel, 'profile')],
                         enabledWhen=lambda i, p: p == 'view')]

        orthoOptsProps = [
            props.Widget('layout', labels=strings.choices['OrthoOpts.layout']), 
            props.Widget('zoom', spin=False, showLimits=False),
            props.Widget('showLabels'),
            props.Widget('showXCanvas'),
            props.Widget('showYCanvas'),
            props.Widget('showZCanvas')]

        lightBoxOptsProps = [
            props.Widget('zax', labels=strings.choices['CanvasOpts.zax']),
            props.Widget('zoom',         showLimits=False, spin=False),
            props.Widget('sliceSpacing', showLimits=False),
            props.Widget('zrange',       showLimits=False),
            props.Widget('highlightSlice'),
            props.Widget('showGridLines')]

        import fsl.fsleyes.views.orthopanel    as orthopanel
        import fsl.fsleyes.views.lightboxpanel as lightboxpanel

        if isinstance(canvasPanel, orthopanel.OrthoPanel):
            panelGroup = 'ortho'
            panelProps = orthoOptsProps
            
        elif isinstance(canvasPanel, lightboxpanel.LightBoxPanel):
            panelGroup = 'lightbox'
            panelProps = lightBoxOptsProps

        self.__widgets.AddGroup('scene' ,    strings.labels[self, 'scene'])
        self.__widgets.AddGroup( panelGroup, strings.labels[self,  panelGroup])

        for dispProp in canvasPanelProps:

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

        for dispProp in sceneOptsProps:

            widget = props.buildGUI(self.__widgets,
                                    opts,
                                    dispProp,
                                    showUnlink=False)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, dispProp.key],
                tooltip=fsltooltips.properties[opts, dispProp.key],
                groupName='scene')

        for dispProp in displayCtxProps:
            widget = props.buildGUI(self.__widgets,
                                    displayCtx,
                                    dispProp,
                                    showUnlink=False)
            
            self.__widgets.AddWidget(
                widget,
                displayName=strings.properties[displayCtx, dispProp.key],
                tooltip=fsltooltips.properties[displayCtx, dispProp.key],
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
