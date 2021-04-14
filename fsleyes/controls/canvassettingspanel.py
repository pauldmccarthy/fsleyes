#!/usr/bin/env python
#
# canvassettingspanel.py - The CanvasSettingsPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasSettingsPanel` class, a *FSLeyes
control* panel which displays settings for a :class:`.CanvasPanel`.
"""


import platform
import collections

import wx

import fsl.data.image                as fslimage
import fsleyes_props                 as props
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.gl                    as fslgl
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


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``CanvasSettingsPanel`` is only intended to be added to
        :class:`.OrthoPanel`, :class:`.LightBoxPanel`, or
        :class:`.Scene3DPanel` views.
        """
        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary of settings to be passed to the
        :meth:`.ViewPanel.togglePanel` method.
        """
        return {'location' : wx.LEFT}


    def __init__(self, parent, overlayList, displayCtx, canvasPanel):
        """Create a ``CanvasSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """

        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         canvasPanel,
                                         kbFocus=True)

        self.__makeTools()


    def destroy(self):
        """Must be called when this ``CanvasSettingsPanel`` is no longer
        needed. Clears references and calls the base class ``destroy`` method.
        """
        super(CanvasSettingsPanel, self).destroy()


    def __makeTools(self):

        displayCtx  = self.displayCtx
        canvasPanel = self.viewPanel
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

        # The highDpi setting is
        # not always relevant
        if not fslgl.WXGLCanvasTarget.canToggleHighDPI():
            sceneOptsProps.pop('highDpi')

        def _displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Nifti):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]

        displayCtxProps = collections.OrderedDict((
            ('displaySpace',
             props.Widget('displaySpace', labels=_displaySpaceOptionName)),
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
            ('zoom',          props.Widget('zoom', showLimits=False)),
            ('showLegend',    props.Widget('showLegend')),
            ('occlusion',     props.Widget('occlusion')),
            ('light',         props.Widget('light')),
            ('showLight',     props.Widget('showLight')),
            ('lightDistance', props.Widget('lightDistance', showLimits=False)),
            ('lightPos',      _genLightPosWidget),
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

        for propName, dispProp in panelProps.items():

            if callable(dispProp):
                widget = dispProp(widgets, opts)
            else:
                widget = props.buildGUI(widgets, opts, dispProp)

            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[opts, propName],
                tooltip=fsltooltips.properties[opts, propName],
                groupName=panelGroup)

        self.setNavOrder(allWidgets)

        widgets.Expand('scene')
        widgets.Expand(panelGroup)


def _genLightPosWidget(parent, opts):
    """Generates a widget for the :attr:`.Scene3DOpts.lightPos` property.
    """
    px, py, pz = props.makeListWidgets(
        parent,
        opts,
        'lightPos',
        slider=True,
        spin=True,
        showLimits=False,
        mousewheel=True)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(px, flag=wx.EXPAND)
    sizer.Add(py, flag=wx.EXPAND)
    sizer.Add(pz, flag=wx.EXPAND)
    return sizer
