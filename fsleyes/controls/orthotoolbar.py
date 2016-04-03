#!/usr/bin/env python
#
# orthotoolbar.py - The OrthoToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoToolBar` class, which is a
:class:`.FSLEyesToolBar` for use with the :class:`.OrthoPanel`.
"""


import props

import fsl.data.image       as fslimage
import fsl.fsleyes.toolbar  as fsltoolbar
import fsl.fsleyes.icons    as fslicons
import fsl.fsleyes.tooltips as fsltooltips
import fsl.fsleyes.actions  as actions
import fsl.fsleyes.strings  as strings


class OrthoToolBar(fsltoolbar.FSLEyesToolBar):
    """The ``OrthoToolBar`` is a :class:`.FSLEyesToolBar` for use with the
    :class:`.OrthoPanel`. An ``OrthoToolBar`` looks something like this:

    
    .. image:: images/orthotoolbar.png
       :scale: 50%
       :align: center

    
    The ``OrthoToolBar`` allows the user to control important parts of the
    :class:`.OrthoPanel` display, and also to display a
    :class:`.CanvasSettingsPanel`, which allows control over all aspects of
    an ``OrthoPanel``.

    The ``OrthoToolBar`` contains controls which modify properties, or run
    actions, defined on the following classes:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.views.orthopanel.OrthoPanel
       ~fsl.fsleyes.displaycontext.orthoopts.OrthoOpts
       ~fsl.fsleyes.profiles.orthoviewprofile.OrthoViewProfile
    """

    
    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``OrthoToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """ 

        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24)
        
        self.orthoPanel = ortho

        # The toolbar has buttons bound to some actions
        # on the Profile  instance - when the profile
        # changes (between 'view' and 'edit'), the
        # Profile instance changes too, so we need
        # to re-create these action buttons. I'm being
        # lazy and just re-generating the entire toolbar.
        ortho.addListener('profile', self._name, self.__makeTools)

        self.__makeTools()


    def __makeTools(self, *a):
        """Called by :meth:`__init__`, and whenever the
        :attr:`.ViewPanel.profile` property changes.

        Re-creates all tools shown on this ``OrthoToolBar``.
        """

        dctx      = self._displayCtx
        ortho     = self.orthoPanel
        orthoOpts = ortho.getSceneOptions()
        profile   = ortho.getCurrentProfile()

        icons = {
            'screenshot'       : fslicons.findImageFile('camera24'),
            'movieMode'        : [
                fslicons.findImageFile('movieHighlight24'),
                fslicons.findImageFile('movie24')],
            'showXCanvas'      : [
                fslicons.findImageFile('sagittalSliceHighlight24'),
                fslicons.findImageFile('sagittalSlice24')],
            'showYCanvas'      : [
                fslicons.findImageFile('coronalSliceHighlight24'),
                fslicons.findImageFile('coronalSlice24')],
            'showZCanvas'      : [
                fslicons.findImageFile('axialSliceHighlight24'),
                fslicons.findImageFile('axialSlice24')],
            'toggleCanvasSettingsPanel' : [
                fslicons.findImageFile('spannerHighlight24'),
                fslicons.findImageFile('spanner24')],

            'layout' : {
                'horizontal' : [
                    fslicons.findImageFile('horizontalLayoutHighlight24'),
                    fslicons.findImageFile('horizontalLayout24')],
                'vertical'   : [
                    fslicons.findImageFile('verticalLayoutHighlight24'),
                    fslicons.findImageFile('verticalLayout24')],
                'grid'       : [
                    fslicons.findImageFile('gridLayoutHighlight24'),
                    fslicons.findImageFile('gridLayout24')]}
        }

        tooltips = {
            'screenshot'   : fsltooltips.actions[   ortho,     'screenshot'],
            'movieMode'    : fsltooltips.properties[ortho,     'movieMode'],
            'zoom'         : fsltooltips.properties[orthoOpts, 'zoom'],
            'layout'       : fsltooltips.properties[orthoOpts, 'layout'],
            'showXCanvas'  : fsltooltips.properties[orthoOpts, 'showXCanvas'],
            'showYCanvas'  : fsltooltips.properties[orthoOpts, 'showYCanvas'],
            'showZCanvas'  : fsltooltips.properties[orthoOpts, 'showZCanvas'],
            'displaySpace' : fsltooltips.properties[dctx,      'displaySpace'],
            'toggleCanvasSettingsPanel' : fsltooltips.actions[
                ortho, 'toggleCanvasSettingsPanel'],
            
        }
        
        targets    = {'screenshot'                : ortho,
                      'movieMode'                 : ortho,
                      'zoom'                      : orthoOpts,
                      'layout'                    : orthoOpts,
                      'showXCanvas'               : orthoOpts,
                      'showYCanvas'               : orthoOpts,
                      'showZCanvas'               : orthoOpts,
                      'displaySpace'              : dctx,
                      'toggleCanvasSettingsPanel' : ortho}

        def displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Nifti1):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]        


        toolSpecs = [

            actions.ToggleActionButton(
                'toggleCanvasSettingsPanel',
                actionKwargs={'floatPane' : True},
                icon=icons['toggleCanvasSettingsPanel'],
                tooltip=tooltips['toggleCanvasSettingsPanel']),
            actions.ActionButton('screenshot',
                                 icon=icons['screenshot'],
                                 tooltip=tooltips['screenshot']),
            props  .Widget(      'showXCanvas',
                                 icon=icons['showXCanvas'],
                                 tooltip=tooltips['showXCanvas']),
            props  .Widget(      'showYCanvas',
                                 icon=icons['showYCanvas'],
                                 tooltip=tooltips['showYCanvas']),
            props  .Widget(      'showZCanvas',
                                 icon=icons['showZCanvas'],
                                 tooltip=tooltips['showZCanvas']),
            props  .Widget(      'layout',
                                 icons=icons['layout'],
                                 tooltip=tooltips['layout']),
            props  .Widget(      'movieMode', 
                                 icon=icons['movieMode'],
                                 tooltip=tooltips['movieMode']), 
            props.Widget(        'displaySpace',
                                 labels=displaySpaceOptionName,
                                 tooltip=tooltips['displaySpace'],
                                 dependencies=[(ortho, 'profile')],
                                 enabledWhen=lambda i, p: p == 'view'),
            props.Widget(        'zoom',
                                 spin=False,
                                 showLimits=False,
                                 tooltip=tooltips['zoom']),
        ]

        tools = []
        
        for spec in toolSpecs:
            widget = props.buildGUI(self, targets[spec.key], spec)

            if spec.key in ('zoom', 'displaySpace'):
                widget = self.MakeLabelledTool(
                    widget,
                    strings.properties[targets[spec.key], spec.key])
            
            tools.append(widget)

        self.SetTools(tools, destroy=True) 
