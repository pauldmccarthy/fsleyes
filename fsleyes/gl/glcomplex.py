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


    def prefilterFunc(self):
        """Overrides :func:`.GLVolume.prefilterFunc`.

        Returns a function which extracts the component to be displayed
        from the image data. Used as the prefilter function by the
        :class:`.ImageTexture`

        See the :attr:`ComplexOpts.component` property.
        """

        opts          = self.opts
        component     = opts.component
        basePrefilter = super().prefilterFunc()

        if   component == 'real':  prefilter = opts.getReal
        elif component == 'imag':  prefilter = opts.getImaginary
        elif component == 'mag':   prefilter = opts.getMagnitude
        else:                      prefilter = opts.getPhase

        if basePrefilter is None: return prefilter
        else:                     return lambda d: prefilter(basePrefilter(d))


    def prefilterRangeFunc(self):
        """Overrides :func:`.GLVolume.prefilterRangeFunc`.

        Returns a function which returns the minimum/maximum of the
        current component. Used as the prefilterRange function by the
        :class:`.ImageTexture`.
        """
        def pr(*a):
            return self.opts.getDataRange()
        return pr


    def __componentChanged(self):
        """Called when the :func:`.ComplexOpts.component` changes.
        Updates the image texture.
        """
        self.imageTexture.set(
            prefilter=self.prefilterFunc(),
            prefilterRange=self.prefilterRangeFunc())
