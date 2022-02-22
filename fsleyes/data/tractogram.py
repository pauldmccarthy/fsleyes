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

    Per-vertex/streamline data can be added via the :meth:`loadVertexData`
    and :meth:`addVertexData` methods. Per-streamline data is duplicated to
    be per-vertex, as this makes it much easier to use in the rendering
{    logic in the :class:`.GLTractogram` class.
    """

    def __init__(self, fname):

        self.dataSource = op.abspath(fname)
        self.name       = op.basename(fname)
        self.tractFile  = nibstrm.load(fname)

        # Data sets associated with each
        # vertex, or with each streamline.
        # Per-streamline data sets are
        # duplicated to be per-vertex on
        # load.
        self.__vertexData = {}

        # Load any per-vertex / per-streamline data
        # which is stored in the streamline file
        tractogram = self.tractFile.tractogram
        for key in tractogram.data_per_streamline.keys():
            data = tractogram.data_per_streamline[key].get_data()
            key  = f'{key} [{self.name}]'
            self.addVertexData(key, data.reshape(-1))
        for key in tractogram.data_per_point.keys():
            data = tractogram.data_per_point[key].get_data()
            key  = f'{key} [{self.name}]'
            self.addVertexData(key, data.reshape(-1))


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
        """Load per-vertex or per-streamline data from a separate file.  The
        data will be accessible via the :meth:`getVertexData` method.
        """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        # TODO mrtrix .tsf scalar format
        vertexData = np.loadtxt(infile).reshape(-1)

        return self.addVertexData(key, vertexData)


    def addVertexData(self, key, vdata):
        """Add some per-vertex or per-streamline data. It can be retrieved via
        :meth:`getVertexData`. ``vdata`` must be a 1D numpy array with
        one value per vertex, or one value per streamline.
        """
        nstrms = self.nstreamlines
        nverts = self.nvertices

        if vdata.ndim != 1 or vdata.shape[0] not in (nverts, nstrms):
            raise ValueError('{}: incompatible vertex/streamline data '
                             'shape: {}'.format(key, vdata.shape))

        # Duplicate per-streamline
        # data to be per-vertex
        if vdata.shape[0] == nstrms:
            vdata = np.repeat(vdata, self.lengths)

        self.__vertexData[key] = vdata


    def getVertexData(self, key):
        """Return the specified per-vertex data. """
        return self.__vertexData[key]


    def vertexDataSets(self):
        """Returns a list of keys for all loaded vertex data sets. """
        return list(self.__vertexData.keys())
