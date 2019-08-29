#!/usr/bin/env python
#
# glcomplex.py - The GLComplex class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLComplex` class, for displaying
:class:`.Image` overlays with a complex data type.
"""

from . import glvolume


class GLComplex(glvolume.GLVolume):
    """The ``GLComplex`` class is a sub-class of :class:`.GLVolume`, specialised
    for displaying :class:`.Image` overlays with a complex data type.


    The only additional behaviour this class provides is refreshing the
    :class:`.ImageTexture` data whenever the :attr:`.ComplexOpts.component`
    property changes.
    """


    def addDisplayListeners(self):
        """Overrides :meth:`VolumeOpts.addDisplayListeners`. Calls that
        method, and also adds additional listeners.
        """
        self.opts.addListener('component', self.name, self.__componentChanged)
        return glvolume.GLVolume.addDisplayListeners(self)


    def removeDisplayListeners(self):
        """Overrides :meth:`VolumeOpts.removeDisplayListeners`. Calls that
        method, and also removes additional listeners.
        """
        self.opts.removeListener('component', self.name)
        return glvolume.GLVolume.removeDisplayListeners(self)


    def __componentChanged(self, *a):
        """Called when the :attr:`component` changes. Updates the image texture
        data.
        """

        opts      = self.opts
        component = opts.component

        # We only want the image texture data
        # to be updated once, despite multiple
        # calls to set() (e.g. from three
        # GLComplex objects in an ortho panel).
        #
        # The ComplexOpts class has static
        # methods for obtaining the real/imag/
        # mag/phase components from the data.
        # We can use these as the texture
        # prefilter function - the image
        # texture will only refresh its data
        # when the prefilter function changes,
        # which will only be on the first call
        # (the prefilter functions are static,
        # so subsequent calls will pass in the
        # same function object)
        if   component == 'real':  func = opts.getReal
        elif component == 'imag':  func = opts.getImaginary
        elif component == 'mag':   func = opts.getMagnitude
        elif component == 'phase': func = opts.getPhase

        self.imageTexture.set(prefilter=func,
                              prefilterRange=func,
                              volRefresh=False)
