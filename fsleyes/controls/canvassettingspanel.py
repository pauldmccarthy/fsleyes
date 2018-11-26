#!/usr/bin/env python
#
# canvassettingspanel.py - The CanvasSettingsPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasSettingsPanel` class, a *FSLeyes
control* panel which displays settings for a :class:`.CanvasPanel`.
"""


import collections

import fsl.data.image                as fslimage
import fsleyes_props                 as props
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.tooltips              as fsltooltips
import fsleyes.strings               as strings


class CanvasSettingsPanel(ctrlpanel.SettingsPanel):
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
       ~fsleyes.displaycontext.Scene3DOpts

    The ``CanvasSettingsPanel`` divides the displayed settings into those
    which are common to all :class:`.CanvasPanel` instances, and those which
    are specific to the :class:`.CanvasPanel` sub-class (i.e.
    :class:`.OrthoPanel`,  :class:`.LightBoxPanel`, or :class:`.Scene3DPanel`).
    """


    def __init__(self, parent, overlayList, displayCtx, frame, canvasPanel):
        """Create a ``CanvasSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """

        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         kbFocus=True)

        self.__canvasPanel = canvasPanel
        self.__makeTools()


    def destroy(self):
        """Must be called when this ``CanvasSettingsPanel`` is no longer
        needed. Clears references and calls the base class ``destroy`` method.
        """
        self.__canvasPanel = None
        super(CanvasSettingsPanel, self).destroy()


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``CanvasSettingsPanel`` is only intended to be added to
        :class:`.OrthoPanel`, :class:`.LightBoxPanel`, or
        :class:`.Scene3DPanel` views.
        """
        from fsleyes.views.orthopanel    import OrthoPanel
        from fsleyes.views.lightboxpanel import LightBoxPanel
        from fsleyes.views.scene3dpanel  import Scene3DPanel
        return [OrthoPanel, LightBoxPanel, Scene3DPanel]


    def __makeTools(self):

        displayCtx  = self.displayCtx
        canvasPanel = self.__canvasPanel
        widgets     = self.getWidgetList()

        canvasPanelProps = collections.OrderedDict((
            ('syncOverlayOrder',   props.Widget('syncOverlayOrder')),
            ('syncLocation',       props.Widget('syncLocation')),
            ('syncOverlayDisplay', props.Widget('syncOverlayDisplay')),
            ('syncOverlayVolume',  props.Widget('syncOverlayVolume')),
            ('movieMode',          props.Widget('movieMode')),
            ('movieSyncRefresh',   props.Widget('movieSyncRefresh')),
            ('movieAxis',
             props.Widget('movieAxis',
                          labels=strings.choices[canvasPanel, 'movieAxis'])),
            ('movieRate',
             props.Widget('movieRate', spin=False, showLimits=False))))


        sceneOptsProps = collections.OrderedDict((
            ('showCursor',   props.Widget('showCursor')),
            ('bgColour',     props.Widget('bgColour')),
            ('fgColour',     props.Widget('fgColour')),
            ('cursorColour', props.Widget('cursorColour')),
            ('performance',
             props.Widget('performance',
                          spin=False,
                          showLimits=False,
                          labels=strings.choices['SceneOpts.performance'])),
            ('highDpi', props.Widget('highDpi')),
            ('showColourBar', props.Widget('showColourBar')),
            ('colourBarLabelSide',
             props.Widget('colourBarLabelSide',
                          labels=strings.choices[
                              'SceneOpts.colourBarLabelSide'],
                          enabledWhen=lambda o: o.showColourBar)),
            ('colourBarLocation',
             props.Widget(
                 'colourBarLocation',
                 labels=strings.choices['SceneOpts.colourBarLocation'],
                 enabledWhen=lambda o: o.showColourBar)),
            ('colourBarSize',
             props.Widget(
                 'colourBarSize',
                 showLimits=False,
                 slider=True,
                 spin=True)),
            ('labelSize', props.Widget('labelSize',
                                       spin=True,
                                       showLimits=False))))

        def _displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Nifti):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]

        displayCtxProps = collections.OrderedDict((
            ('displaySpace',
             props.Widget('displaySpace',
                          labels=_displaySpaceOptionName,
                          dependencies=[(canvasPanel, 'profile')],
                          enabledWhen=lambda i, p: p == 'view')),
            ('radioOrientation', props.Widget('radioOrientation'))))

        orthoOptsProps = collections.OrderedDict((
            ('layout',
             props.Widget('layout',
                          labels=strings.choices['OrthoOpts.layout'])),
            ('zoom',        props.Widget('zoom', showLimits=False)),
            ('showLabels',  props.Widget('showLabels')),
            ('cursorGap',   props.Widget('cursorGap')),
            ('showXCanvas', props.Widget('showXCanvas')),
            ('showYCanvas', props.Widget('showYCanvas')),
            ('showZCanvas', props.Widget('showZCanvas'))))

        lightBoxOptsProps = collections.OrderedDict((
            ('zax',
             props.Widget('zax', labels=strings.choices['CanvasOpts.zax'])),
            ('zoom',
             props.Widget('zoom', showLimits=False, spin=False)),
            ('sliceSpacing',   props.Widget('sliceSpacing', showLimits=False)),
            ('zrange',         props.Widget('zrange',       showLimits=False)),
            ('highlightSlice', props.Widget('highlightSlice')),
            ('showGridLines',  props.Widget('showGridLines'))))

        scene3dOptsProps = collections.OrderedDict((
            ('zoom',       props.Widget('zoom', showLimits=False)),
            ('showLegend', props.Widget('showLegend')),
            ('light',      props.Widget('light')),
            ('occlusion',  props.Widget('occlusion')),
        ))

        import fsleyes.views.orthopanel    as orthopanel
        import fsleyes.views.lightboxpanel as lightboxpanel
        import fsleyes.views.scene3dpanel  as scene3dpanel

        if isinstance(canvasPanel, orthopanel.OrthoPanel):
            panelGroup = 'ortho'
            panelProps = orthoOptsProps

        elif isinstance(canvasPanel, lightboxpanel.LightBoxPanel):
            panelGroup = 'lightbox'
            panelProps = lightBoxOptsProps
        elif isinstance(canvasPanel, scene3dpanel.Scene3DPanel):
            panelGroup = '3d'
            panelProps = scene3dOptsProps

            # We hide some options in 3D
            sceneOptsProps .pop('performance')
            displayCtxProps.pop('displaySpace')
            displayCtxProps.pop('radioOrientation')

        widgets.AddGroup('scene' ,    strings.labels[self, 'scene'])
        widgets.AddGroup( panelGroup, strings.labels[self,  panelGroup])

        allWidgets = []

        for dispProp in canvasPanelProps.values():

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

        opts = canvasPanel.sceneOpts

        for dispProp in sceneOptsProps.values():

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

        for dispProp in displayCtxProps.values():
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

        for dispProp in panelProps.values():

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
