#!/usr/bin/env python
#
# lightboxlabels.py - The LightBoxLabels class,
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightboxLabels` class, which manages
location labels for a :class :`.LightBoxCanvas`.
"""


import numpy as np

import fsl.utils.cache as cache


class LightBoxLabels:
    """The ``LightBoxLabels`` class manages text labels on a
    :class:`.LightBoxCanvas`.

    :class:`.LightBoxCanvas` objects create a :class:`LightBoxLabels` instance,
    and call the :meth:`refreshLabels` method directly.
    """


    def __init__(self, canvas):
        """
        """
        self.__name   = f'{id(self)}_{type(self).__name__}'
        self.__canvas = canvas
        self.__labels = cache.Cache(500, lru=True)


    def destroy(self):
        """Must be called when this ``LightboxLabels`` instance is no longer
        needed. Destroys all of the :class:`.TextAnnotation` objects used
        for displaying slice locations.
        """
        for text in self.__labels.values():
            text.destroy()
        self.__labels = None
        self.__canvas = None


    def getLabel(self, zpos, label):
        """Return a :class:`.TextAnnotation` object with the given label. If
        one does not exist, it is created.
        """

        text = self.__labels.get((zpos, label), None)

        if text is None:
            text = self.__canvas.getAnnotations().text(label, hold=True)
            self.__labels[zpos, label] = text

        return text


    def getZFormat(self, space, overlay):
        """Return a format string suitable for formatting the Z location
        in the label space coordinate system, with respect to the given
        overlay.
        """
        canvas = self.__canvas
        dctx   = canvas.displayCtx
        ref    = dctx.getReferenceImage(overlay)

        if ref is None:
            space = 'world'

        if space == 'voxel': fmt = '{} = {:.0f}'
        else:                fmt = '{} = {:.2f}'

        return fmt


    def getZAxis(self, space, overlay):
        """Identify the Z axis in the label space coordinate system, with
        respect to the given overlay, which most closelyt matches the Z axis
        in the :class:`.LightBoxCanvas` display coordinate system.
        """

        canvas = self.__canvas
        zax    = canvas.opts.zax
        dctx   = canvas.displayCtx
        ref    = dctx.getReferenceImage(overlay)

        # non-NIFTI overlay, e.g. mesh, tractogram.
        # The display coordinate system is aligned
        # with the overlay world coordinate system.
        if ref is None:
            return zax, 'XYZ'[zax]

        # Find the axis in the destination coordinate system
        # which most closely matches the canvas depth axis.
        opts  = dctx.getOpts(ref)
        axmap = ref.axisMapping(opts.getTransform('display', space))
        zax   = abs(axmap[zax]) - 1
        axlbl = 'XYZ'[zax]

        return zax, axlbl


    def getZLocation(self, space, overlay, slc):
        """Calculate the Z location in the label space coordinate system, with
        respect to the given overlay, which corresponds to the given
        :class:`.LightBoxCanvas` slice.
        """

        canvas = self.__canvas
        copts  = canvas.opts
        dctx   = canvas.displayCtx
        bounds = dctx.bounds
        ref    = dctx.getReferenceImage(overlay)

        # Get the display coord sys (d) location
        # for the centre of this slice. If None,
        # we're out of display bounds.
        dpos = canvas.sliceToWorld(slc)
        if dpos is None:
            return None, None

        # Convert dpos into the destination coordinate
        # system (w) - this gives us our Z location.
        #
        # We can only transform into the destination
        # coordinate system for NIFTI overlays, or
        # overlays with a NIFTI reference.
        if ref is not None:
            opts = dctx.getOpts(ref)
            wpos = opts.transformCoords(dpos, 'display', space)
        else:
            wpos = dpos

        # And also transform into the lb canvas coordinate
        # system (c) normalising the canvas x/y to [0, 1],
        # as we need it in relative proportions for label
        # positioning.
        cpos   = canvas.worldToCanvas(dpos)
        if cpos is None:
            return None, None

        cx, cy = cpos
        cy     = cy + 0.5 * bounds.getLen(copts.yax)
        cx     = (cx - copts.displayBounds.xlo) / copts.displayBounds.xlen
        cy     = (cy - copts.displayBounds.ylo) / copts.displayBounds.ylen

        return wpos, (cx, cy)


    def refreshLabels(self):
        """Updates slice labels on the :class:`.LightBoxCanvas`. """

        canvas  = self.__canvas
        copts   = canvas.opts
        space   = copts.labelSpace
        nslices = len(canvas.zposes)
        dctx    = canvas.displayCtx
        ovl     = dctx.getSelectedOverlay()

        for text in self.__labels.values():
            text.enabled = False

        if space == 'none':
            return

        if ovl is None:
            return

        fmt        = self.getZFormat(space, ovl)
        zax, axlbl = self.getZAxis(  space, ovl)

        for i in range(nslices):

            wpos, cpos = self.getZLocation(space, ovl, i)

            if wpos is None or cpos is None:
                continue

            wpos = wpos[zax]

            # Try and prevent near-0 values
            # being formatted as "-0.00"
            if np.isclose(wpos, 0, atol=1e-3):
                wpos = 0

            text           = fmt.format(axlbl, wpos)
            label          = self.getLabel(wpos, text)
            label.fontSize = copts.labelSize
            label.colour   = copts.fgColour
            label.enabled  = True
            label.x        = cpos[0]
            label.y        = cpos[1]
            label.off      = (0, -5)
            label.halign   = 'centre'
            label.valign   = 'top'
