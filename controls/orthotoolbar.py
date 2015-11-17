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
import fsl.data.strings     as strings


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
            'movieMode'        : fslicons.findImageFile('movie24'),
            'showXCanvas'      : fslicons.findImageFile('sagittalSlice24'),
            'showYCanvas'      : fslicons.findImageFile('coronalSlice24'),
            'showZCanvas'      : fslicons.findImageFile('axialSlice24'),
            'showMoreSettings' : fslicons.findImageFile('gear24'),

            'resetZoom'    : fslicons.findImageFile('resetZoom24'),
            'centreCursor' : fslicons.findImageFile('centre24'),

            'layout' : {
                'horizontal' : fslicons.findImageFile('horizontalLayout24'),
                'vertical'   : fslicons.findImageFile('verticalLayout24'),
                'grid'       : fslicons.findImageFile('gridLayout24'),
            }
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
            'resetZoom'    : fsltooltips.actions[   profile,   'resetZoom'],
            'centreCursor' : fsltooltips.actions[   profile,   'centreCursor'],
            'showMoreSettings' : fsltooltips.actions[self, 'showMoreSettings'],
            
        }
        
        targets    = {'screenshot'       : ortho,
                      'movieMode'        : ortho,
                      'zoom'             : orthoOpts,
                      'layout'           : orthoOpts,
                      'showXCanvas'      : orthoOpts,
                      'showYCanvas'      : orthoOpts,
                      'showZCanvas'      : orthoOpts,
                      'displaySpace'     : dctx,
                      'resetZoom'        : profile,
                      'centreCursor'     : profile,
                      'showMoreSettings' : self}

        def displaySpaceOptionName(opt):

            if isinstance(opt, fslimage.Image):
                return opt.name
            else:
                return strings.choices['DisplayContext.displaySpace'][opt]        


        toolSpecs = [

            actions.ActionButton('showMoreSettings',
                                 icon=icons['showMoreSettings'],
                                 tooltip=tooltips['showMoreSettings']),
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
            actions.ActionButton('resetZoom',
                                 icon=icons['resetZoom'],
                                 tooltip=tooltips['resetZoom']),
            actions.ActionButton('centreCursor',
                                 icon=icons['centreCursor'],
                                 tooltip=tooltips['centreCursor']),
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


    @actions.ToggleAction
    def showMoreSettings(self, *a):
        """Opens a :class:`.CanvasSettingsPanel` for the
        :class:`.OrthoPanel` that owns this ``OrthoToolBar``.

        The ``CanvasSettingsPanel`` is opened as a floating pane - see the
        :meth:`.ViewPanel.togglePanel` method.
        """
        
        import canvassettingspanel
        self.orthoPanel.togglePanel(canvassettingspanel.CanvasSettingsPanel,
                                    self.orthoPanel,
                                    floatPane=True)
