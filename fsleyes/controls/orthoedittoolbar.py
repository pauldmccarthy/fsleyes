#!/usr/bin/env python
#
# orthoedittoolbar.py - The OrthoEditToolBar
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditToolBar`, a
:class:`.ControlToolBar` which displays controls for editing :class:`.Image`
instances in an :class:`.OrthoPanel`.
"""


import logging

import wx

import fsleyes_props                 as props
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.toolbar               as fsltoolbar
import fsleyes.icons                 as fslicons
import fsleyes.tooltips              as fsltooltips
import fsleyes.strings               as strings

import fsleyes.controls.displayspacewarning  as dswarning
from   fsleyes.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)


class OrthoEditToolBar(ctrlpanel.ControlToolBar):
    """The ``OrthoEditToolBar`` is a :class:`.ControlToolBar` which displays
    controls for editing :class:`.Image` instances in an :class:`.OrthoPanel`.

    An ``OrthoEditToolBar`` looks something like this:


    .. image:: images/orthoedittoolbar.png
       :scale: 50%
       :align: center


    The ``OrthoEditToolBar`` exposes properties and actions which are defined
    on the :class:`.OrthoEditProfile` class, and allows the user to:

     - Change the :class:`.OrthoPanel` profile  between ``view`` and ``edit``
       mode (see the :attr:`.ViewPanel.profile` property). When in ``view``
       mode, all of the other controls are hidden.

     - Undo/redo changes to the selection and to :class:`.Image` instances.

     - Clear and fill the current selection.

     - Switch between a 2D and 3D selection cursor.

     - Change the selection cursor size.

     - Create a new mask/ROI :class:`.Image` from the current selection.

     - Switch between regular *select* mode, and *select by intensity* mode,
       and adjust the select by intensity mode settings.


    All of the controls shown on an ``OrthoEditToolBar`` instance are defined
    in the :attr:`_TOOLBAR_SPECS` dictionary.
    """


    selint = props.Boolean(default=False)
    """This property allows the user to change the :class:`.OrthoEditProfile`
    between ``sel`` mode, and ``selint`` mode.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create an ``OrthoEditToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          frame,
                                          height=24,
                                          kbFocus=True)

        self.__orthoPanel = ortho
        self.__dsWarning = dswarning.DisplaySpaceWarning(
            self,
            self.overlayList,
            self.displayCtx,
            self.frame,
            strings.messages[self, 'dsWarning'],
            'not like overlay',
            'overlay')

        ortho.addListener('profile', self.name, self.__profileChanged)

        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``OrthoEditToolBar`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.ControlToolBar.destroy` method.
        """
        self.__orthoPanel.removeListener('profile', self.name)
        self.__dsWarning.destroy()

        self.__orthoPanel = None
        self.__dsWarning  = None

        ctrlpanel.ControlToolBar.destroy(self)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OrthoEditToolBar`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


    def __profileChanged(self, *a):
        """Called when the :attr:`.ViewPanel.profile` property of the
        :class:`.OrthoPanel` changes. Shows/hides edit controls accordingly.
        """

        self.ClearTools(destroy=True, postevent=False)

        ortho      = self.__orthoPanel
        profile    = ortho.profile
        profileObj = ortho.getCurrentProfile()

        if profile != 'edit':
            self.__dsWarning.Show(False)
            return

        allTools   = []
        allWidgets = []

        for specGroup in _TOOLBAR_SPECS:

            if specGroup == 'div':
                allTools.append(fsltoolbar.ToolBarDivider(self,
                                                          height=24,
                                                          orient=wx.VERTICAL))
                continue

            groupWidgets = []
            isGroup      = isinstance(specGroup, list)

            if isGroup:
                parent = wx.Panel(self)

            else:
                parent    = self
                specGroup = [specGroup]

            for spec in specGroup:

                widget = props.buildGUI(parent, profileObj, spec)

                if not isGroup and spec.label is not None:
                    widget = self.MakeLabelledTool(widget,
                                                   spec.label,
                                                   expand=True)

                allWidgets  .append(widget)
                groupWidgets.append(widget)

            # Assuming here that all
            # widgets have labels
            if isGroup:

                sizer = wx.FlexGridSizer(2, 2, 0, 0)
                parent.SetSizer(sizer)

                labels = [s.label for s in specGroup]
                labels = [wx.StaticText(parent, label=l) for l in labels]

                for w, l in zip(groupWidgets, labels):
                    sizer.Add(l, flag=wx.EXPAND)
                    sizer.Add(w, flag=wx.EXPAND)

                allTools.append(parent)

            else:
                allTools.append(groupWidgets[0])

        self.SetTools(   [self.__dsWarning] + allTools)
        self.setNavOrder(allWidgets)


_LABELS = {

    'selectionCursorColour'  : strings.properties[OrthoEditProfile,
                                                  'selectionCursorColour'],
    'selectionOverlayColour' : strings.properties[OrthoEditProfile,
                                                  'selectionOverlayColour'],
    'selectionSize'          : strings.properties[OrthoEditProfile,
                                                  'selectionSize'],
    'intensityThres'         : strings.properties[OrthoEditProfile,
                                                  'intensityThres'],
    'searchRadius'           : strings.properties[OrthoEditProfile,
                                                  'searchRadius'],
    'fillValue'              : strings.properties[OrthoEditProfile,
                                                  'fillValue'],
    'targetImage'            : strings.properties[OrthoEditProfile,
                                                  'targetImage'],
}
"""This dictionary contains labels for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_ICONS = {


    'drawMode'  : [fslicons.findImageFile('drawModeHighlight24'),
                   fslicons.findImageFile('drawMode24'),
                   fslicons.findImageFile('selectModeHighlight24'),
                   fslicons.findImageFile('selectMode24')],

    'mode' : {
        'nav'    : [
            fslicons.findImageFile('addHighlight24'),
            fslicons.findImageFile('add24'),
        ],
        'sel'    : [
            fslicons.findImageFile('pencilHighlight24'),
            fslicons.findImageFile('pencil24'),
        ],
        'desel'  : [
            fslicons.findImageFile('eraserHighlight24'),
            fslicons.findImageFile('eraser24'),
        ],
        'fill' : [
            fslicons.findImageFile('bucketHighlight24'),
            fslicons.findImageFile('bucket24'),
        ],
        'selint' : [
            fslicons.findImageFile('selectByIntensityHighlight24'),
            fslicons.findImageFile('selectByIntensity24'),
        ],
    },
    'selectionIs3D' : [
        fslicons.findImageFile('selection3DHighlight24'),
        fslicons.findImageFile('selection3D24'),
        fslicons.findImageFile('selection2DHighlight24'),
        fslicons.findImageFile('selection2D24')],

    'limitToRadius' :  [
        fslicons.findImageFile('radiusHighlight24'),
        fslicons.findImageFile('radius24')],
    'localFill' :  [
        fslicons.findImageFile('localsearchHighlight24'),
        fslicons.findImageFile('localsearch24')],
    'selint' :  [
        fslicons.findImageFile('selectByIntensityHighlight24'),
        fslicons.findImageFile('selectByIntensity24')],
}
"""This dictionary contains icons for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_TOOLTIPS = {
    'drawMode'       : fsltooltips.properties['OrthoEditProfile.'
                                              'drawMode'],

    'mode'           : fsltooltips.properties['OrthoEditProfile.mode'],
    'selectionIs3D'  : fsltooltips.properties['OrthoEditProfile.'
                                              'selectionIs3D'],

    'limitToRadius'  : fsltooltips.properties['OrthoEditProfile.'
                                              'limitToRadius'],
    'searchRadius'   : fsltooltips.properties['OrthoEditProfile.'
                                              'searchRadius'],
    'localFill'      : fsltooltips.properties['OrthoEditProfile.localFill'],
    'selectionSize'  : fsltooltips.properties['OrthoEditProfile.'
                                              'selectionSize'],
    'fillValue'      : fsltooltips.properties['OrthoEditProfile.fillValue'],
    'intensityThres' : fsltooltips.properties['OrthoEditProfile.'
                                              'intensityThres'],

    'targetImage'    : fsltooltips.properties['OrthoEditProfile.targetImage'],
}
"""This dictionary contains tooltips for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


def _targetImageName(image):
    if image is None: return 'None'
    else:             return image.name


_TOOLBAR_SPECS  = [

    props.Widget(
        'drawMode',
        toggle=False,
        icon=_ICONS['drawMode'],
        tooltip=_TOOLTIPS['drawMode'],
        style=wx.HORIZONTAL),
    'div',
    props.Widget(
        'mode',
        icons=_ICONS['mode'],
        tooltip=_TOOLTIPS['mode'],
        fixChoices=['nav', 'sel', 'desel', 'fill', 'selint']),
    'div',
    props.Widget(
        'selectionIs3D',
        icon=_ICONS['selectionIs3D'],
        tooltip=_TOOLTIPS['selectionIs3D'],
        toggle=False,
        dependencies=['mode'],
        enabledWhen=lambda p, m: m != 'fill'),
    props.Widget(
        'limitToRadius',
        icon=_ICONS['limitToRadius'],
        tooltip=_TOOLTIPS['limitToRadius'],
        dependencies=['mode'],
        enabledWhen=lambda p, m: m == 'selint'),
    props.Widget(
        'localFill',
        icon=_ICONS['localFill'],
        tooltip=_TOOLTIPS['localFill'],
        dependencies=['mode'],
        enabledWhen=lambda p, m: m == 'selint'),
    [props.Widget(
        'selectionSize',
        spin=True,
        slider=False,
        showLimits=False,
        spinWidth=3,
        label=_LABELS['selectionSize'],
        tooltip=_TOOLTIPS['selectionSize']),
     props.Widget(
         'fillValue',
         label=_LABELS['fillValue'],
         tooltip=_TOOLTIPS['fillValue'],
         slider=False,
         spinWidth=3,
         increment=1)],

    [props.Widget(
        'intensityThres',
        slider=True,
        spin=True,
        showLimits=False,
        spinWidth=6,
        label=_LABELS['intensityThres'],
        tooltip=_TOOLTIPS['intensityThres'],
        dependencies=['mode'],
        enabledWhen=lambda p, m: m == 'selint'),
     props.Widget(
         'searchRadius',
         slider=True,
         spin=True,
         showLimits=False,
         spinWidth=6,
         label=_LABELS['searchRadius'],
         tooltip=_TOOLTIPS['searchRadius'],
         dependencies=['mode', 'limitToRadius'],
         enabledWhen=lambda p, m, r: m == 'selint' and r)],

    props.Widget('targetImage',
                 label=_LABELS['targetImage'],
                 tooltip=_TOOLTIPS['targetImage'],
                 labels=_targetImageName,
                 dependencies=['drawMode'],
                 enabledWhen=lambda p, dm: not dm)
]
"""This list contains specifications for all of the tools shown in an
:class:`OrthoEditToolBar`, in the order that they are shown.

Some specs are grouped together into sub-lists - these will be laid out
vertically on the toolbar.
"""
