#!/usr/bin/env python
#
# canvassettingspanel.py - The CanvasSettingsPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasSettingsPanel` class, a *FSLeyes
control* panel which displays settings for a :class:`.CanvasPanel`.
"""


import fsl.data.image      as fslimage
import fsleyes_props       as props
import fsleyes.panel       as fslpanel
import fsleyes.tooltips    as fsltooltips
import fsleyes.strings     as strings


class CanvasSettingsPanel(fslpanel.FSLeyesSettingsPanel):
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

       ~fsleyes.views.canvaspanel.CanvasPanel
       ~fsleyes.displaycontext.SceneOpts
       ~fsleyes.displaycontext.OrthoOpts
       ~fsleyes.displaycontext.LightBoxOpts

    The ``CanvasSettingsPanel`` divides the displayed settings into those
    which are common to all :class:`.CanvasPanel` instances, and those which
    are specific to the :class:`.CanvasPanel` sub-class (i.e.
    :class:`.OrthoPanel` or :class:`.LightBoxPanel`).
    """


    def __init__(self, parent, overlayList, displayCtx, frame, canvasPanel):
        """Create a ``CanvasSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """

        fslpanel.FSLeyesSettingsPanel.__init__(self,
                                               parent,
                                               overlayList,
                                               displayCtx,
                                               frame,
                                               kbFocus=True)

        self.__canvasPanel = canvasPanel
        self.__makeTools()


    def __makeTools(self):

        displayCtx  = self._displayCtx
        canvasPanel = self.__canvasPanel
        widgets     = self.getWidgetList()

        canvasPanelProps = [
            props.Widget('syncOverlayOrder'),
            props.Widget('syncLocation'),
            props.Widget('syncOverlayDisplay'),
            props.Widget('movieMode'),
            props.Widget('movieAxis',
                         labels=strings.choices[canvasPanel, 'movieAxis']),
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

            if isinstance(opt, fslimage.Nifti):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]

        displayCtxProps = [
            props.Widget('displaySpace',
                         labels=_displaySpaceOptionName,
                         dependencies=[(canvasPanel, 'profile')],
                         enabledWhen=lambda i, p: p == 'view'),
            props.Widget('radioOrientation')]

        orthoOptsProps = [
            props.Widget('layout', labels=strings.choices['OrthoOpts.layout']),
            props.Widget('zoom', showLimits=False),
            props.Widget('showLabels'),
            props.Widget('labelColour'),
            props.Widget('labelSize',
                         spin=True,
                         showLimits=False,
                         dependencies=['showLabels'],
                         enabledWhen=lambda i, s: s),
            props.Widget('cursorGap'),
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

        import fsleyes.views.orthopanel    as orthopanel
        import fsleyes.views.lightboxpanel as lightboxpanel

        if isinstance(canvasPanel, orthopanel.OrthoPanel):
            panelGroup = 'ortho'
            panelProps = orthoOptsProps

        elif isinstance(canvasPanel, lightboxpanel.LightBoxPanel):
            panelGroup = 'lightbox'
            panelProps = lightBoxOptsProps

        widgets.AddGroup('scene' ,    strings.labels[self, 'scene'])
        widgets.AddGroup( panelGroup, strings.labels[self,  panelGroup])

        allWidgets = []

        for dispProp in canvasPanelProps:

            widget = props.buildGUI(widgets,
                                    canvasPanel,
                                    dispProp,
                                    showUnlink=False)

            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[canvasPanel, dispProp.key],
                tooltip=fsltooltips.properties[canvasPanel, dispProp.key],
                groupName='scene')

        opts = canvasPanel.getSceneOptions()

        for dispProp in sceneOptsProps:

            widget = props.buildGUI(widgets,
                                    opts,
                                    dispProp,
                                    showUnlink=False)

            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, dispProp.key],
                tooltip=fsltooltips.properties[opts, dispProp.key],
                groupName='scene')

        for dispProp in displayCtxProps:
            widget = props.buildGUI(widgets,
                                    displayCtx,
                                    dispProp,
                                    showUnlink=False)

            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[displayCtx, dispProp.key],
                tooltip=fsltooltips.properties[displayCtx, dispProp.key],
                groupName='scene')

        for dispProp in panelProps:

            widget = props.buildGUI(widgets,
                                    opts,
                                    dispProp,
                                    showUnlink=False)

            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, dispProp.key],
                tooltip=fsltooltips.properties[opts, dispProp.key],
                groupName=panelGroup)

        self.setNavOrder(allWidgets)

        widgets.Expand('scene')
        widgets.Expand(panelGroup)
