#!/usr/bin/env python
#
# giftiopts.py - The GiftiOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GiftiOpts` class, which contains settings
for displaying a :class:`.GiftiSurface` overlay.
"""


from . import meshopts


class GiftiOpts(meshopts.MeshOpts):
    """The :class:`GiftiOpts` class, which contains settings for displaying
    a :class:`.GiftiSurface` overlay.

    Currently (as of FSLeyes |version|), the ``GiftiOpts`` class is identical
    to the :class:`.MeshOpts` class (from which it derives), with the exception
    that the initial value of the :attr:`.MeshOpts.coordSpace` property is
    set to ``'affine'``.
    """
    
    def __init__(self, *args, **kwargs):
        """Create a ``GiftiOpts`` instance.

        All arguments are passed to the :class:`.MeshOpts` constructor.
        """

        self.getProp('coordSpace').setConstraint(self, 'default', 'affine')
        self.coordSpace = 'affine'

        meshopts.MeshOpts.__init__(self, *args, **kwargs)

        self.__vertexData = None
        self.addListener('vertexData', self.name, self.__vertexDataChanged)


    def __vertexDataChanged(self, *a):
        """Called when the :attr:`vertexData` property changes. Attempts
        to load the specified data.
        """

        import nibabel as nib

        try:
            norms = nib.load(self.vertexData)
            norms = norms.darrays[0].data

            self.displayRange.xmin = norms.min()
            self.displayRange.xmax = norms.max()

            self.__vertexData = norms

        except:
            self.__vertexData = None


    def getVertexData(self):
        """Returns the :attr:`.MeshOpts.vertexData`, if some is loaded.
        Returns ``None`` otherwise.
        """
        return self.__vertexData
