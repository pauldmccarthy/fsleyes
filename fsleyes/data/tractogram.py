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

import functools as ft
import os.path   as op

import numpy                as np
import nibabel.streamlines  as nibstrm

import fsl.transform.affine as affine


ALLOWED_EXTENSIONS     = ['.tck', '.trk']
EXTENSION_DESCRIPTIONS = ['MRtrix .tck file', 'TrackVis .trk file']


class Tractogram:
    """The ``Tractogram`` class is a thin wrapper around a
    ``nibabel.streamlines.Tractogram`` object, with a few methods for managing
    per-vertex and per-streamline data.
    """

    def __init__(self, fname):

        self.dataSource = op.abspath(fname)
        self.name       = op.basename(fname)
        self.tractFile  = nibstrm.load(fname)

        # Data sets associated with each vertex,
        # or with each streamline. These can be
        # loded from the tractogram file, or
        # loaded from separate files.
        self.__vertexData       = {}
        self.__streamlineData   = {}
        self.__streamlinePVData = {}

        # Load any per-vertex / per-streamline data
        # which is stored in the streamline file
        tractogram = self.tractFile.tractogram
        for skey in tractogram.data_per_streamline.keys():
            sdata = tractogram.data_per_streamline[skey].get_data()
            skey  = f'{skey} [{self.name}]'
            self.addStreamlineData(skey, sdata.reshape(-1))
        for vkey in tractogram.data_per_point.keys():
            vdata = tractogram.data_per_point[vkey].get_data()
            vkey  = f'{vkey} [{self.name}]'
            self.addVertexData(vkey, vdata.reshape(-1))


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


    @property
    @ft.lru_cache()
    def orientation(self):
        """Calculates and returns an orientation vector for every vertex of
        every streamline in the tractogram.

        The orientation assigned to a vertex is just the difference between
        that vertex and the previous vertex in the streamline. The first
        vertex in a streamline is given the same orientation as the second
        (i.e. o0 = o1 = (v1 - v0)).
        """

        verts   = self.vertices
        offsets = self.offsets
        orients = np.zeros(verts.shape, dtype=np.float32)

        diffs               = verts[1:, :] - verts[:-1, :]
        orients[1:,      :] = affine.normalise(diffs)
        orients[offsets, :] = orients[offsets + 1, :]

        return orients


    def loadVertexData(self, infile, key=None):
        """Load per-vertex or per-streamline data from a separate file.
        The data will be accessible via the :meth:`getVertexData` or
        :meth:`getStreamlineData` methods, depending on its shape.
        """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        # TODO mrtrix .tsf scalar format
        vertexData = np.loadtxt(infile).reshape(-1)

        if len(vertexData) == self.nvertices:
            return self.addVertexData(key, vertexData)
        else:
            return self.addStreamlineData(key, vertexData)


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


    def getStreamlineDataPerVertex(self, key):
        """Return the specified per-streamline data, with each value repeated
        for every vertex.
        """

        vdata = self.__streamlinePVData.get(key, None)
        if vdata is None:
            sdata = self.getStreamlineData(key)
            vdata = np.repeat(sdata, self.lengths)
            self.__streamlinePVData[key] = vdata

        return vdata


    def vertexDataSets(self):
        """Returns a list of keys for all loaded vertex data sets. """
        return list(self.__vertexData.keys())


    def streamlineDataSets(self):
        """Returns a list of keys for all loaded streamline data sets. """
        return list(self.__streamlineData.keys())
