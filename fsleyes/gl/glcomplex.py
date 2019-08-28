#!/usr/bin/env python
#
# glcomplex.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from . import glvolume


class GLComplex(glvolume.GLVolume):
    """
    """

    def addDisplayListeners(self):
        self.opts.addListener('component', self.name, self.__componentChanged)
        return glvolume.GLVolume.addDisplayListeners(self)


    def removeDisplayListeners(self):
        self.opts.removeListener('component', self.name)
        return glvolume.GLVolume.removeDisplayListeners(self)


    def __componentChanged(self, *a):
        self.imageTexture.set(prefilter=self.opts.getComponent,
                              prefilterRange=self.opts.getComponent,
                              volRefresh=False)
