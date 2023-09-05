#!/usr/bin/env python
#
# ortholabels.py - The OrthoLabels class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoLabels` class, which manages
anatomical and location labels for an :class:`.OrthoPanel`.

This logic is independent from the :class:`.OrthoPanel` so it can be used in
off-screen rendering (see :mod:`.render`).
"""


import fsl.data.image     as fslimage
import fsl.data.constants as constants


class OrthoLabels:
    """The ``OrthoLabels`` class manages anatomical orientation and location
    labels which are displayed on a set of three :class:`.SliceCanvas`
    instances, one for each plane in the display coordinate system, typically
    within an :class:`.OrthoPanel`.


    The ``OrthoLabels`` class uses :class:`.annotations.Text` annotations,
    showing the user:

     - the anatomical orientation of the display on each canvas.
     - the current location on a selected csanvas.

    Anatomical labels can be toggled on and off via the
    :attr:`.OrthoOpts.showLabels` property, and location via the
    :attr:`.OrthoOpts.showLocation` priperty.

    Anatomical labels are only shown if the currently selected overlay (as
    dictated by the :attr:`.DisplayContext.selectedOverlay` property) is a
    :class:`.Image` instance, **or** the :meth:`.DisplayOpts.referenceImage`
    property for the currently selected overlay returns an :class:`.Image`
    instance.

    If the currently selected overlay is an :class:`.Image`, both voxel and
    world coordinates are shown. Otherwise only world coordinates are shown.
    """


    def __init__(self,
                 overlayList,
                 displayCtx,
                 orthoOpts,
                 *canvases):
        """Create an ``OrthoLabels`` instance.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg orthoOpts:   :class:`.OrthoOpts` instance which contains
                          display settings.
        :arg canvases:    The :class:`.SliceCanvas` instances to be labelled.
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__orthoOpts   = orthoOpts
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList

        # labels is a list of dicts, one
        # for each canvas, containing Text
        # annotations to show anatomical
        # orientation and location
        annots = [{} for c in canvases]

        self.__canvases = canvases
        self.__annots   = annots

        # Create the Text annotations
        for side in ('left', 'right', 'top', 'bottom', 'location'):
            for canvas, cannots in zip(canvases, annots):
                annot         = canvas.getAnnotations()
                cannots[side] = annot.text('', 0, 0, hold=True)

        # Initialise the display properties
        # of each Text annotation
        for cannots in annots:
            cannots['left']    .halign = 'left'
            cannots['right']   .halign = 'right'
            cannots['top']     .halign = 'centre'
            cannots['bottom']  .halign = 'centre'
            cannots['location'].halign = 'left'

            cannots['left']    .valign = 'centre'
            cannots['right']   .valign = 'centre'
            cannots['top']     .valign = 'top'
            cannots['bottom']  .valign = 'bottom'
            cannots['location'].valign = 'top'

            cannots['left']    .x = 0.0
            cannots['left']    .y = 0.5
            cannots['right']   .x = 1.0
            cannots['right']   .y = 0.5
            cannots['bottom'].  x = 0.5
            cannots['bottom']  .y = 0.0
            cannots['top']     .x = 0.5
            cannots['top']     .y = 1.0
            cannots['location'].x = 0.0
            cannots['location'].y = 1.0

            # Keep cannots 5 pixels away
            # from the canvas edges
            cannots['left']    .off = ( 5,  0)
            cannots['right']   .off = (-5,  0)
            cannots['top']     .off = ( 0, -5)
            cannots['bottom']  .off = ( 0,  5)
            cannots['location'].off = ( 5, -5)

        # Add listeners to properties
        # that need to trigger a label
        # refresh.
        name = self.__name

        # Make immediate so the label
        # annotations get updated before
        # a panel refresh occurs (where
        # the latter is managed by the
        # OrthoPanel).
        labelArgs = {
            'name'      : name,
            'callback'  : self.refreshLabels,
            'immediate' : True
        }
        anatomyArgs              = dict(labelArgs)
        anatomyArgs['callback']  = self.refreshAnatomy
        locationArgs             = dict(labelArgs)
        locationArgs['callback'] = self.refreshLocation

        for c in canvases:
            c.opts.addListener('invertX', **anatomyArgs)
            c.opts.addListener('invertY', **anatomyArgs)

        orthoOpts  .addListener('showLabels',       **labelArgs)
        orthoOpts  .addListener('labelSize',        **labelArgs)
        orthoOpts  .addListener('fgColour',         **labelArgs)
        displayCtx .addListener('selectedOverlay',  **labelArgs)
        displayCtx .addListener('displaySpace',     **labelArgs)
        displayCtx .addListener('radioOrientation', **anatomyArgs)
        orthoOpts  .addListener('showLocation',     **locationArgs)
        displayCtx .addListener('location',         **locationArgs)
        overlayList.addListener('overlays', name, self.__overlayListChanged)


    def destroy(self):
        """Must be called when this ``OrthoLabels`` instance is no longer
        needed.
        """

        name        = self.__name
        overlayList = self.__overlayList
        displayCtx  = self.__displayCtx
        orthoOpts   = self.__orthoOpts
        canvases    = self.__canvases
        annots      = self.__annots

        self.__overlayList = None
        self.__displayCtx  = None
        self.__orthoOpts   = None
        self.__canvases    = None
        self.__annots      = None

        orthoOpts  .removeListener('showLabels',       name)
        orthoOpts  .removeListener('showLocation',     name)
        orthoOpts  .removeListener('labelSize',        name)
        orthoOpts  .removeListener('fgColour',         name)
        displayCtx .removeListener('selectedOverlay',  name)
        displayCtx .removeListener('displaySpace',     name)
        displayCtx .removeListener('radioOrientation', name)
        displayCtx .removeListener('location',         name)
        overlayList.removeListener('overlays',         name)

        for c in canvases:
            c.opts.removeListener('invertX', name)
            c.opts.removeListener('invertY', name)

        # The _overlayListChanged method adds
        # listeners to individual overlays,
        # so we have to remove them too
        for ovl in overlayList:
            opts = displayCtx.getOpts(ovl)
            opts.removeListener('bounds', name)

        # Destroy the Text annotations
        for a in annots:
            for text in a.values():
                text.destroy()


    def refreshLabels(self, *a):
        """Forces the orientation and location annotations to be refreshed.
        All arguments are ignored.
        """
        self.refreshAnatomy()
        self.refreshLocation()


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Registers a listener
        on the attr:.DisplayOpts.bounds` property of every overlay in the list,
        so the labels are refreshed when any overlay bounds change.
        """

        for ovl in self.__overlayList:

            opts = self.__displayCtx.getOpts(ovl)

            # Update anatomy labels when
            # overlay bounds change
            opts.addListener('bounds',
                             self.__name,
                             self.refreshLabels,
                             overwrite=True)

        # When the list becomes empty, or
        # an overlay is added to an empty
        # list, the DisplayContext.selectedOverlay
        # will not change, and __refreshLabels
        # will thus not get called. So we call
        # it here.
        if len(self.__overlayList) in (0, 1):
            self.refreshLabels()


    def refreshLocation(self, *a):
        """Refreshs the label displaying the current cursor location. """
        displayCtx = self.__displayCtx
        sopts      = self.__orthoOpts
        annots     = self.__annots
        overlay    = displayCtx.getSelectedOverlay()
        ref        = displayCtx.getReferenceImage(overlay)
        opts       = None
        wx, wy, wz = displayCtx.worldLocation

        if overlay is None:
            return

        for cannots, canvas in zip(annots, 'XYZ'):
            showLoc = sopts.showLocation == canvas
            cannots['location'].enabled = showLoc

        if sopts.showLocation == 'no':
            return

        if   sopts.showLocation == 'X': locLbl = annots[0]['location']
        elif sopts.showLocation == 'Y': locLbl = annots[1]['location']
        elif sopts.showLocation == 'Z': locLbl = annots[2]['location']


        if ref is None:
            locstr     = f'{wx:0.2f} {wy:0.2f} {wz:0.2f}'
        else:
            opts       = displayCtx.getOpts(ref)
            vx, vy, vz = opts.getVoxel()
            locstr     = f'{wx:0.2f} {wy:0.2f} {wz:0.2f}' + \
                         f'\n[voxel {vx} {vy} {vz}]'

        locLbl.fontSize = sopts.labelSize
        locLbl.colour   = sopts.fgColour
        locLbl.text     = locstr


    def refreshAnatomy(self, *a):
        """Updates the attributes of the :class:`.Text` anatomical orientation
        annotations on each :class:`.SliceCanvas`.
        """

        displayCtx = self.__displayCtx
        sopts      = self.__orthoOpts
        canvases   = self.__canvases
        annots     = self.__annots
        overlay    = displayCtx.getSelectedOverlay()
        showLabels = sopts.showLabels and (overlay is not None)

        for cannots, canvas in zip(annots, 'XYZ'):
            cannots['left']    .enabled = showLabels
            cannots['right']   .enabled = showLabels
            cannots['top']     .enabled = showLabels
            cannots['bottom']  .enabled = showLabels

        if not showLabels:
            return

        opts = displayCtx.getOpts(overlay)

        # Calculate all of the xyz
        # labels for this overlay
        labels, orients              = opts.getLabels()
        xlo, ylo, zlo, xhi, yhi, zhi = labels
        vertOrient                   = len(xlo) > 1
        fontSize                     = sopts.labelSize
        fgColour                     = tuple(sopts.fgColour)

        # If any axis orientation is unknown, make
        # the foreground colour red, to highlight
        # the unknown orientation.
        if constants.ORIENT_UNKNOWN in orients:
            fgColour = (1, 0, 0, 1)

        # A list, with one entry for each canvas,
        # and with each entry of the form:
        #
        #   [[xlo, xhi], [ylo, yhi]]
        #
        # containing the low/high labels for the
        # horizontal (x) and vertical (y) canvas
        # axes.
        canvasLabels = []
        for canvas in canvases:

            cax = 'xyz'[canvas.opts.zax]

            if   cax == 'x': clabels = [[ylo, yhi], [zlo, zhi]]
            elif cax == 'y': clabels = [[xlo, xhi], [zlo, zhi]]
            elif cax == 'z': clabels = [[xlo, xhi], [ylo, yhi]]

            if canvas.opts.invertX: clabels[0] = [clabels[0][1], clabels[0][0]]
            if canvas.opts.invertY: clabels[1] = [clabels[1][1], clabels[1][0]]

            canvasLabels.append(clabels)

        # Update the text annotation properties
        for canvas, cannots, clabels in zip(canvases, annots, canvasLabels):

            cax = 'xyz'[canvas.opts.zax]

            cannots['left']  .text = clabels[0][0]
            cannots['right'] .text = clabels[0][1]
            cannots['bottom'].text = clabels[1][0]
            cannots['top']   .text = clabels[1][1]

            if   cax == 'x': show = sopts.showXCanvas
            elif cax == 'y': show = sopts.showYCanvas
            elif cax == 'z': show = sopts.showZCanvas

            for side in ['left', 'right', 'bottom', 'top']:

                cannots[side].enabled  = show
                cannots[side].fontSize = fontSize
                cannots[side].colour   = fgColour

            if vertOrient:
                cannots['left'] .angle = 90
                cannots['right'].angle = 90

        for canvas in canvases:
            canvas.Refresh()
