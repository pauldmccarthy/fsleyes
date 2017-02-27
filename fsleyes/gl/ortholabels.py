#!/usr/bin/env python
#
# ortholabels.py - The OrthoLabels class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoLabels` class, which manages
anatomical orientation labels for an :class:`.OrthoPanel`.

This logic is independent from the :class:`.OrthoPanel` so it can be used in
off-screen rendering (see :mod:`.render`).
"""


import fsl.data.constants as constants
import fsleyes.strings    as strings


class OrthoLabels(object):
    """The ``OrthoLabels`` class manages anatomical orientation labels which 
    are displayed on a set of three :class:`.SliceCanvas` instances, one for 
    each plane in the display coordinate system, typically within an
    :class:`.OrthoPanel`.

    The ``OrthoLabels`` class uses :class:`.annotations.Text` annotations,
    showing the user the anatomical orientation of the display on each
    canvas. These labels are only shown if the currently selected overlay (as
    dicated by the :attr:`.DisplayContext.selectedOverlay` property) is a
    :class:`.Image` instance, **or** the
    :meth:`.DisplayOpts.getReferenceImage` method for the currently selected
    overlay returns an :class:`.Image` instance.
    """


    def __init__(self,
                 overlayList,
                 displayCtx,
                 orthoOpts,
                 xcanvas,
                 ycanvas,
                 zcanvas):
        """Create an ``OrthoLabels`` instance.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg orthoOpts:   :class:`.OrthoOpts` instance which contains
                           display settings.
        :arg xcanvas:     :class:`.SliceCanvas` for the X plane. 
        :arg ycanvas:     :class:`.SliceCanvas` for the Y plane. 
        :arg zcanvas:     :class:`.SliceCanvas` for the Z plane.
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__orthoOpts   = orthoOpts
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__xcanvas     = xcanvas
        self.__ycanvas     = ycanvas
        self.__zcanvas     = zcanvas

        # Labels (Text annotations) to show
        # anatomical orientation, stored in
        # a dict for each canvas
        self.__xlabels = {}
        self.__ylabels = {}
        self.__zlabels = {}

        xannot = self.__xcanvas.getAnnotations()
        yannot = self.__ycanvas.getAnnotations()
        zannot = self.__zcanvas.getAnnotations()

        for side in ('left', 'right', 'top', 'bottom'):
            self.__xlabels[side] = xannot.text("", 0, 0, width=2, hold=True)
            self.__ylabels[side] = yannot.text("", 0, 0, width=2, hold=True)
            self.__zlabels[side] = zannot.text("", 0, 0, width=2, hold=True)

        for labels in [self.__xlabels, self.__ylabels, self.__zlabels]:
            labels['left']  .halign = 'left'
            labels['right'] .halign = 'right'
            labels['top']   .halign = 'centre'
            labels['bottom'].halign = 'centre'

            labels['left']  .valign = 'centre'
            labels['right'] .valign = 'centre'
            labels['top']   .valign = 'top'
            labels['bottom'].valign = 'bottom'

            labels['left']  .xpos = 0
            labels['left']  .ypos = 0.5
            labels['right'] .xpos = 1.0
            labels['right'] .ypos = 0.5
            labels['bottom'].xpos = 0.5
            labels['bottom'].ypos = 0
            labels['top']   .xpos = 0.5
            labels['top']   .ypos = 1.0

            # Keep labels 5 pixels away
            # from the canvas edges
            labels['left']  .xoff =  5
            labels['right'] .xoff = -5
            labels['top']   .yoff = -5
            labels['bottom'].yoff =  5

        name = self.__name

        # Make immediate so the label
        # annotations get updated before
        # a panel refresh occurs (where
        # the latter is managed by the
        # OrthoPanel).
        refreshArgs = {
            'name'      : name,
            'callback'  : self.__refreshLabels,
            'immediate' : True
        }

        orthoOpts  .addListener('showLabels',       **refreshArgs)
        orthoOpts  .addListener('labelSize',        **refreshArgs)
        orthoOpts  .addListener('labelColour',      **refreshArgs)
        displayCtx .addListener('selectedOverlay',  **refreshArgs)
        displayCtx .addListener('displaySpace',     **refreshArgs)
        displayCtx .addListener('radioOrientation', **refreshArgs)
        xcanvas    .addListener('invertX',          **refreshArgs)
        xcanvas    .addListener('invertY',          **refreshArgs)
        ycanvas    .addListener('invertX',          **refreshArgs)
        ycanvas    .addListener('invertY',          **refreshArgs)
        zcanvas    .addListener('invertX',          **refreshArgs)
        zcanvas    .addListener('invertY',          **refreshArgs)
        overlayList.addListener('overlays', name, self.__overlayListChanged)

        
    def destroy(self):
        """Must be called when this ``OrthoLabels`` instance is no longer
        needed.
        """

        name        = self.__name
        overlayList = self.__overlayList
        displayCtx  = self.__displayCtx
        orthoOpts   = self.__orthoOpts
        xcanvas     = self.__xcanvas
        ycanvas     = self.__ycanvas
        zcanvas     = self.__zcanvas
        
        orthoOpts  .removeListener('showLabels',       name)
        orthoOpts  .removeListener('labelSize',        name)
        orthoOpts  .removeListener('labelColour',      name)
        displayCtx .removeListener('selectedOverlay',  name)
        displayCtx .removeListener('displaySpace',     name)
        displayCtx .removeListener('radioOrientation', name)
        xcanvas    .removeListener('invertX',          name)
        xcanvas    .removeListener('invertY',          name)
        ycanvas    .removeListener('invertX',          name)
        ycanvas    .removeListener('invertY',          name)
        zcanvas    .removeListener('invertX',          name)
        zcanvas    .removeListener('invertY',          name)
        overlayList.removeListener('overlays',         name)

        # The _overlayListChanged method adds
        # listeners to individual overlays,
        # so we have to remove them too
        for ovl in self._overlayList:
            opts = self._displayCtx.getOpts(ovl)
            opts.removeListener('bounds', self._name)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Registers a listener
        on the attr:.DisplayOpts.bounds` property of every overlay in the list,
        so the labels are refreshed when any overlay bounds change.
        """
        
        for i, ovl in enumerate(self.__overlayList):

            opts = self.__displayCtx.getOpts(ovl)

            # Update anatomy labels when 
            # overlay bounds change
            opts.addListener('bounds',
                             self.__name,
                             self.__refreshLabels,
                             overwrite=True)

        # When the list becomes empty, or
        # an overlay is added to an empty
        # list, the DisplayContext.selectedOverlay
        # will not change, and __refreshLabels
        # will thus not get called. So we call
        # it here.
        if len(self.__overlayList) in (0, 1):
            self.__refreshLabels()


    def __refreshLabels(self, *a):
        """Updates the attributes of the :class:`.Text` anatomical orientation
        annotations on each :class:`.SliceCanvas`.
        """

        displayCtx = self.__displayCtx
        sopts      = self.__orthoOpts
        overlay    = displayCtx.getSelectedOverlay()
        ref        = displayCtx.getReferenceImage(overlay)
        
        xcanvas = self.__xcanvas
        ycanvas = self.__ycanvas
        zcanvas = self.__zcanvas
        xlabels = self.__xlabels
        ylabels = self.__ylabels
        zlabels = self.__zlabels

        for lbls in [xlabels, ylabels, zlabels]:
            for text in lbls.values():
                text.enabled = sopts.showLabels and (overlay is not None)

        if not sopts.showLabels or overlay is None:
            return

        labels, orients, vertOrient  = self.__getLabels(ref)
        xlo, ylo, zlo, xhi, yhi, zhi = labels

        fontSize = sopts.labelSize
        bgColour = tuple(sopts.bgColour)
        fgColour = tuple(sopts.labelColour)

        # If any axis orientation is unknown, and the
        # the background colour is black or white,
        # make the foreground colour red, to highlight
        # the unknown orientation. It's too difficult
        # to do this for any background colour.
        if constants.ORIENT_UNKNOWN in orients and \
           bgColour in ((0, 0, 0, 1), (1, 1, 1, 1)):
            fgColour = (1, 0, 0, 1) 

        xcxlo, xcxhi = ylo, yhi
        xcylo, xcyhi = zlo, zhi
        ycxlo, ycxhi = xlo, xhi
        ycylo, ycyhi = zlo, zhi
        zcxlo, zcxhi = xlo, xhi
        zcylo, zcyhi = ylo, yhi

        if xcanvas.invertX: xcxlo, xcxhi = xcxhi, xcxlo
        if xcanvas.invertY: xcylo, xcyhi = xcyhi, xcylo
        if ycanvas.invertX: ycxlo, ycxhi = ycxhi, ycxlo
        if ycanvas.invertY: ycylo, ycyhi = ycyhi, ycylo
        if zcanvas.invertX: zcxlo, zcxhi = zcxhi, zcxlo
        if zcanvas.invertY: zcylo, zcyhi = zcyhi, zcylo

        xlabels['left']  .text = xcxlo
        xlabels['right'] .text = xcxhi
        xlabels['bottom'].text = xcylo
        xlabels['top']   .text = xcyhi
        ylabels['left']  .text = ycxlo
        ylabels['right'] .text = ycxhi
        ylabels['bottom'].text = ycylo
        ylabels['top']   .text = ycyhi
        zlabels['left']  .text = zcxlo
        zlabels['right'] .text = zcxhi
        zlabels['bottom'].text = zcylo
        zlabels['top']   .text = zcyhi 

        shows  = [sopts.showXCanvas, sopts.showYCanvas, sopts.showZCanvas] 
        labels = [xlabels,           ylabels,           zlabels]

        for show, lbls in zip(shows, labels):
            
            lbls['left']  .enabled = show
            lbls['right'] .enabled = show
            lbls['bottom'].enabled = show
            lbls['top']   .enabled = show
            
            if not show:
                continue

            lbls['left']  .fontSize = fontSize
            lbls['right'] .fontSize = fontSize
            lbls['bottom'].fontSize = fontSize
            lbls['top']   .fontSize = fontSize
            lbls['left']  .colour   = fgColour
            lbls['right'] .colour   = fgColour
            lbls['bottom'].colour   = fgColour
            lbls['top']   .colour   = fgColour

            if vertOrient:
                lbls['left'] .angle = 90
                lbls['right'].angle = 90

        
    def __getLabels(self, refImage):
        """Generates some orientation labels to use for the given reference
        image (assumed to be a :class:`.Nifti` overlay, or ``None``).

        Returns a tuple containing:

          - The ``(xlo, ylo, zlo, xhi, yhi, zhi)`` bounds
          - The ``(xorient, yorient, zorient)`` orientations (see
            :meth:`.Image.getOrientation`)
          - A boolean flag which indicates whether the label should be oriented
            vertically (``True``), or horizontally (``False``).
        """

        if refImage is None:
            return ('??????', [constants.ORIENT_UNKNOWN] * 3, False) 
        
        opts = self.__displayCtx.getOpts(refImage)

        vertOrient = False
        xorient    = None
        yorient    = None
        zorient    = None
        
        # If we are displaying in voxels/scaled voxels,
        # and this image is not the current display
        # image, then we do not show anatomical
        # orientation labels, as there's no guarantee
        # that all of the loaded overlays are in the
        # same orientation, and it can get confusing.
        if opts.transform in ('id', 'pixdim', 'pixdim-flip') and \
           self.__displayCtx.displaySpace != refImage:
            xlo        = 'Xmin'
            xhi        = 'Xmax'
            ylo        = 'Ymin'
            yhi        = 'Ymax'
            zlo        = 'Zmin'
            zhi        = 'Zmax'
            vertOrient = True

        # Otherwise we assume that all images
        # are aligned to each other, so we
        # estimate the current image's orientation
        # in the display coordinate system
        else:

            xform      = opts.getTransform('world', 'display')
            xorient    = refImage.getOrientation(0, xform)
            yorient    = refImage.getOrientation(1, xform)
            zorient    = refImage.getOrientation(2, xform)

            xlo        = strings.anatomy['Nifti', 'lowshort',  xorient]
            ylo        = strings.anatomy['Nifti', 'lowshort',  yorient]
            zlo        = strings.anatomy['Nifti', 'lowshort',  zorient]
            xhi        = strings.anatomy['Nifti', 'highshort', xorient]
            yhi        = strings.anatomy['Nifti', 'highshort', yorient]
            zhi        = strings.anatomy['Nifti', 'highshort', zorient]

        return ((xlo, ylo, zlo, xhi, yhi, zhi), 
                (xorient, yorient, zorient),
                vertOrient)
