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
import fsl.data.constants   as constants


ALLOWED_EXTENSIONS     = ['.tck', '.trk']
EXTENSION_DESCRIPTIONS = ['MRtrix .tck file', 'TrackVis .trk file']


class Tractogram:
    """The ``Tractogram`` class is a thin wrapper around a
    ``nibabel.streamlines.Tractogram`` object, with a few methods for managing
    per-vertex and per-streamline data.

    Per-vertex/streamline data can be added via the :meth:`loadVertexData`
    and :meth:`addVertexData` methods. Per-streamline data is duplicated to
    be per-vertex, as this makes it much easier to use in the rendering
    logic in the :class:`.GLTractogram` class.
    """

    def __init__(self, fname):

        self.dataSource = op.abspath(fname)
        self.name       = op.basename(fname)
        self.tractFile  = nibstrm.load(fname)

        # Bounding box is calculsted on first
        # call to bounds(), then cached for
        # subsequent calls.
        self.__bounds = None

        # Data sets associated with each
        # vertex, or with each streamline.
        # Per-streamline data sets are
        # duplicated to be per-vertex on
        # load.
        self.__vertexData = {}

        # Load any per-vertex / per-streamline data
        # which is stored in the streamline file

        # nibabel supports storage of multiple
        # values per key per streamline/vertex,
        # but we currently only support scalar
        # values (i.e. one value per key per
        # streamline/vertex), and discard all
        # but the first value.
        tractogram = self.tractFile.tractogram
        for key in tractogram.data_per_streamline.keys():
            data = tractogram.data_per_streamline[key]
            self.addVertexData(key, data[:, 0].reshape(-1))
        for key in tractogram.data_per_point.keys():
            data = tractogram.data_per_point[key].get_data()
            self.addVertexData(key, data[:, 0].reshape(-1))


    def __str__(self):
        return f'{type(self).__name__}(self.name)'


    @property
    def affine(self):
        """Returns an affine transformation matrix which can be used to
        transform the streamline vertices into an RAS / millimetre-based
        coordinate system.
        """
        return self.tractFile.affine


    @property
    def bounds(self):
        """Returns the bounding box of all streamlines as a tuple of
        ``((xlo, ylo, zlo),  (xhi, yhi, zhi))`` values.
        """
        if self.__bounds is None:
            data = self.tractFile.streamlines.get_data()
            self.__bounds = (data.min(axis=0), data.max(axis=0))
        return self.__bounds


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
    def orientation(self):
        """Returns codes indicating the orientation of the coordinate
        system in which the streamline vertices are defined.

        The codes that are returned are only valid if the :meth:`affine`
        transformation is applied to the vertex coordinates.
        """
        # Currently always RAS - mrtrix coordinates are always RAS
        # (and the affine is typically an identity transform), and
        # trackvis files contain a coordinate-to-RAS affine (which
        # is further adjusted by nibabel to encode a half-voxel shift):
        #
        #   - https://mrtrix.readthedocs.io/en/latest/getting_started/\
        #       image_data.html?highlight=format#coordinate-system
        #   - http://trackvis.org/docs/?subsect=fileformat
        #   - https://nipy.org/nibabel/reference/\
        #       nibabel.streamlines.html#trkfile
        return [constants.ORIENT_L2R,
                constants.ORIENT_P2A,
                constants.ORIENT_I2S]


    @property
    @ft.lru_cache()
    def vertexOrientations(self):
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


    def subset(self, indices):
        """Extract a sub-set of streamlines using the given ``indices`` into
        the :meth:`offsets` / :meth:`lengths` arrays. The provided ``indices``
        must be sorted.

        :returns: A tuple of numpy arrays:
                    - New streamline vertices
                    - Offsets
                    - Lengths
                    - Indices into the full :meth:`vertices` array.
        """

        offsets = self.offsets[indices]
        lengths = self.lengths[indices]

        vertIdxs = np.zeros(np.sum(lengths), dtype=np.uint32)
        i        = 0
        for o, l in zip(offsets, lengths):
            vertIdxs[i:i + l] = np.arange(o, o + l, dtype=np.uint32)
            i                += l

        vertices       = self.vertices[vertIdxs]
        newOffsets     = np.zeros(len(offsets), dtype=np.int32)
        newOffsets[1:] = np.cumsum(lengths)[:-1]

        return vertices, newOffsets, lengths, vertIdxs


    def loadVertexData(self, infile, key=None):
        """Load per-vertex or per-streamline data from a separate file.  The
        data will be accessible via the :meth:`getVertexData` method.
        """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        # TODO mrtrix .tsf scalar format?
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
