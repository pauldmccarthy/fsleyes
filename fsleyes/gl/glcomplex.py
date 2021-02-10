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


    def refreshImageTexture(self):
        """Overrides :meth:`.GLVolume.refreshImageTexture`. Calls that
        method, passing it a prefilter function to extract the complex
        component from the image data.
        """
        pfunc  = self.getPrefilterFunc()
        prfunc = self.getPrefilterRangeFunc()
        glvolume.GLVolume.refreshImageTexture(self,
                                              prefilter=pfunc,
                                              prefilterRange=prfunc)


    def getPrefilterFunc(self):
        """Returns a function which extracts the component to be displayed
        from the image data. Used as the prefilter function by the
        :class:`.ImageTexture`

        See the :attr:`ComplexOpts.component` property.
        """

        opts      = self.opts
        component = opts.component

        if   component == 'real':  return opts.getReal
        elif component == 'imag':  return opts.getImaginary
        elif component == 'mag':   return opts.getMagnitude
        elif component == 'phase': return opts.getPhase


    def getPrefilterRangeFunc(self):
        """Returns a function which returns the minimum/maximum of the
        current component. Used as the prefilterRange function by the
        :class:`.ImageTexture`.
        """
        def pr(*a):
            return self.opts.getDataRange()
        return pr


    def __componentChanged(self, *a):
        """Called when the :attr:`component` changes. Updates the image texture
        data.
        """
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
        pfunc  = self.getPrefilterFunc()
        prfunc = self.getPrefilterRangeFunc()
        self.imageTexture.set(prefilter=pfunc,
                              prefilterRange=prfunc,
                              volRefresh=False)
