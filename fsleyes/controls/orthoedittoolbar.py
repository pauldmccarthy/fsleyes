#!/usr/bin/env python
#
# orthoedittoolbar.py - The OrthoEditToolBar
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditToolBar`, a
:class:`.FSLeyesToolBar` which displays controls for editing :class:`.Image`
instances in an :class:`.OrthoPanel`.
"""


import logging

import props

import fsleyes.toolbar  as fsltoolbar
import fsleyes.icons    as fslicons
import fsleyes.tooltips as fsltooltips
import fsleyes.strings  as strings

from fsleyes.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)


class OrthoEditToolBar(fsltoolbar.FSLeyesToolBar):
    """The ``OrthoEditToolBar`` is a :class:`.FSLeyesToolBar` which displays
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
        fsltoolbar.FSLeyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           frame,
                                           height=24,
                                           kbFocus=True)

        self.__orthoPanel = ortho

        ortho.addListener('profile', self._name, self.__profileChanged)

        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``OrthoEditToolBar`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLeyesToolBar.destroy` method.
        """
        self.__orthoPanel.removeListener('profile', self._name)
        fsltoolbar.FSLeyesToolBar.destroy(self)


    def __profileChanged(self, *a):
        """Called when the :attr:`.ViewPanel.profile` property of the
        :class:`.OrthoPanel` changes. Shows/hides edit controls accordingly.
        """

        self.ClearTools(destroy=True, postevent=False)
        
        ortho      = self.__orthoPanel
        profile    = ortho.profile
        profileObj = ortho.getCurrentProfile()
        
        if profile != 'edit':
            return
                
        tools = []
        nav   = []

        for spec in _TOOLBAR_SPECS:

            target    = profileObj
            widget    = props.buildGUI(self, target, spec)
            navWidget = widget

            if spec.label is not None:
                widget = self.MakeLabelledTool(widget, spec.label)
                
            tools.append(widget)
            nav  .append(navWidget)

        self.SetTools(tools)
        self.setNavOrder(nav)


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
}
"""This dictionary contains labels for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_ICONS = {

    'mode'                    : {
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
        'selint' : [
            fslicons.findImageFile('selectByIntensityHighlight24'),
            fslicons.findImageFile('selectByIntensity24'),
        ],
    },
    'selectionIs3D'           : [
        fslicons.findImageFile('selection3DHighlight24'),
        fslicons.findImageFile('selection3D24'),
        fslicons.findImageFile('selection2DHighlight24'),
        fslicons.findImageFile('selection2D24')],
    
    'limitToRadius'           :  [
        fslicons.findImageFile('radiusHighlight24'),
        fslicons.findImageFile('radius24')],
    'localFill'               :  [
        fslicons.findImageFile('localsearchHighlight24'),
        fslicons.findImageFile('localsearch24')],
    'selint'                  :  [
        fslicons.findImageFile('selectByIntensityHighlight24'),
        fslicons.findImageFile('selectByIntensity24')],
}
"""This dictionary contains icons for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""


_TOOLTIPS = {
    'mode'                    : fsltooltips.properties['OrthoEditProfile.'
                                                       'mode'],
    'selectionIs3D'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'selectionIs3D'],

    'selint'                  : fsltooltips.properties['OrthoEditToolBar.'
                                                       'selint'],
    'limitToRadius'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'limitToRadius'],
    'searchRadius'            : fsltooltips.properties['OrthoEditProfile.'
                                                       'searchRadius'],
    'localFill'               : fsltooltips.properties['OrthoEditProfile.'
                                                       'localFill'],
    'selectionSize'           : fsltooltips.properties['OrthoEditProfile.'
                                                       'selectionSize'],
    'fillValue'               : fsltooltips.properties['OrthoEditProfile.'
                                                       'fillValue'],
    'intensityThres'          : fsltooltips.properties['OrthoEditProfile.'
                                                       'intensityThres'],
}
"""This dictionary contains tooltips for some :class:`OrthoEditToolBar`
controls. It is referenced in the :attr:`_TOOLBAR_SPECS` dictionary.
"""




_TOOLBAR_SPECS  = [

    props.Widget(
        'mode',
        icons=_ICONS['mode'],
        tooltips=_TOOLTIPS['mode'],
        fixChoices=['nav', 'sel', 'desel', 'selint']),
    props.Widget(
        'selectionIs3D',
        icon=_ICONS['selectionIs3D'],
        tooltip=_TOOLTIPS['selectionIs3D'],
        toggle=False),
    props.Widget(
        'limitToRadius',
        icon=_ICONS['limitToRadius'],
        tooltip=_TOOLTIPS['limitToRadius'],
        enabledWhen=lambda p: p.mode == 'selint'),
    props.Widget(
        'localFill',
        icon=_ICONS['localFill'],
        tooltip=_TOOLTIPS['localFill'],
        enabledWhen=lambda p: p.mode == 'selint'),
    props.Widget(
        'selectionSize',
        label=_LABELS['selectionSize'],
        tooltip=_TOOLTIPS['selectionSize']),
    props.Widget(
        'fillValue',
        label=_LABELS['fillValue'],
        tooltip=_TOOLTIPS['fillValue'],
        slider=False,
        increment=1),
    props.Widget(
        'intensityThres',
        slider=True,
        spin=False,
        label=_LABELS['intensityThres'],
        tooltip=_TOOLTIPS['intensityThres'],
        enabledWhen=lambda p: p.mode == 'selint'),
    props.Widget(
        'searchRadius',
        slider=True,
        spin=False,
        label=_LABELS['searchRadius'],
        tooltip=_TOOLTIPS['searchRadius'],
        enabledWhen=lambda p: p.mode == 'selint' and p.limitToRadius),

    props.Widget('targetImage'),
    props.Widget('drawMode'),
]
"""This list contains specifications for all of the tools shown in an
:class:`OrthoEditToolBar`, in the order that they are shown.
"""
