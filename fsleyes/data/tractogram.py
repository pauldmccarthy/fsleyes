#!/usr/bin/env python
#
# tractogram.py - The Tractogram class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Tractogram` class, which is used by FSLeyes
for displaying streamline tractography ``.trk`` or ``.tck`` files.
"""

import os.path as op

import nibabel.streamlines as nibstrm


ALLOWED_EXTENSIONS     = ['.tck', '.trk']
EXTENSION_DESCRIPTIONS = ['MRtrix .tck file', 'TrackVis .trk file']


class Tractogram:
    def __init__(self, fname):

        self.dataSource = op.abspath(fname)
        self.name       = op.basename(fname)
        self.tractFile  = nibstrm.load(fname)


    @property
    def bounds(self):
        """Returns the bounding box of all streamlines as a tuple of
        ``((xlo, ylo, zlo),  (xhi, yhi, zhi))`` values.
        """
        data = self.tractFile.streamlines.get_data()
        return (data.min(axis=0), data.max(axis=0))


    @property
    def numStreamlines(self):
        return len(self.tractFile.streamlines)


    @property
    def vertices(self):
        return self.tractFile.streamlines.get_data()


    @property
    def lengths(self):
        return self.tractFile.streamlines._lengths


    @property
    def offsets(self):
        return self.tractFile.streamlines._offsets
