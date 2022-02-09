#!/usr/bin/env python
#
# tractogram.py - The Tractogram class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Tractogram` class, which is used by FSLeyes
for displaying streamline tractography ``.trk`` or ``.tck`` files.

The ``Tractogram`` class is just a thin wrapper around a
``nibabel.streamlines.Tractogram`` object.
"""

import os.path as op

import numpy               as np
import nibabel.streamlines as nibstrm


ALLOWED_EXTENSIONS     = ['.tck', '.trk']
EXTENSION_DESCRIPTIONS = ['MRtrix .tck file', 'TrackVis .trk file']


class Tractogram:

    def __init__(self, fname):

        self.dataSource = op.abspath(fname)
        self.name       = op.basename(fname)
        self.tractFile  = nibstrm.load(fname)

        # Data sets associated with each vertex,
        # or with each streamline. These can be
        # loded from the tractogram file, or
        # loaded from separate files.
        self.__vertexData     = {}
        self.__streamlineData = {}

        # TODO load vertex/streamline data from nib
        # object (i.e. trk scalars/properties)


    @property
    def bounds(self):
        """Returns the bounding box of all streamlines as a tuple of
        ``((xlo, ylo, zlo),  (xhi, yhi, zhi))`` values.
        """
        data = self.tractFile.streamlines.get_data()
        return (data.min(axis=0), data.max(axis=0))


    @property
    def vertices(self):
        """Returns a numpy array of shape ``(n, 3)`` containing all
        vertices of all streamlines.
        """
        return self.tractFile.streamlines.get_data()


    @property
    def lengths(self):
        """Returns a 1D numpy array containing the lengths (number of vertices)
        of all streamlines.
        """
        return self.tractFile.streamlines._lengths


    @property
    def offsets(self):
        """Returns a 1D numpy array containing the offsets into
        :meth:`vertices` for all streamlines.
        """
        return self.tractFile.streamlines._offsets


    @property
    def nstreamlines(self):
        """Returns the number of streamlines. """
        return len(self.tractFile.streamlines)


    @property
    def nvertices(self):
        """Returns the total number of vertices across all streamlines. """
        return len(self.vertices)


    def loadVertexData(self, infile, key=None):
        """Load per-vertex data from a separate file. """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        # TODO mrtrix .tsf scalar format
        vertexData = np.loadtxt(infile)

        return self.addVertexData(key, vertexData)


    def loadStreamlineData(self, infile, key=None):
        """Load per-streamline data from a separate file. """
        infile = op.abspath(infile)

        if key is None:
            key = infile

        strmData = np.loadtxt(infile)

        return self.addStreamlineData(key, strmData)


    def addVertexData(self, key, vdata):
        """Add some per-vertex data. It can be retrieved via
        :meth:`getVertexData`. ``vdata`` must be a 1D numpy array with
        one value per vertex.
        """
        nvertices = self.nvertices
        if vdata.ndim != 1 or vdata.shape[0] != nvertices:
            raise ValueError('{}: incompatible vertex data '
                             'shape: {}'.format(key, vdata.shape))
        self.__vertexData[key] = vdata


    def addStreamlineData(self, key, sdata):
        """Add some per-streamline data. It can be retrieved via
        :meth:`getStreamlineData`.  ``sdata`` must be a 1D numpy array with
        one value per streamline.
        """
        nstrms = self.nstreamlines
        if sdata.ndim != 1 or sdata.shape[0] != nstrms:
            raise ValueError('{}: incompatible streamline data '
                             'shape: {}'.format(key, sdata.shape))
        self.__streamlineData[key] = sdata


    def getVertexData(self, key):
        """Return the specified per-vertex data. """
        return self.__vertexData[key]


    def getStreamlineData(self, key):
        """Return the specified per-streamline data. """
        return self.__streamlineData[key]
