#!/usr/bin/env python
#
# mif.py - The MIFImage class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.MIFImage` class, for loading MRtrix3
``.mif`` image files.
"""


import io
import gzip
import os.path as op
import string

from typing import Any

import numpy as np

from   fsl.transform import affine
import fsl.data.image as    fslimage


MIFHeader = dict[str, Any]


ALLOWED_EXTENSIONS = ['.mih', '.mif', '.mif.gz']
"""Allowed file extensions for MIF images. """

EXTENSION_DESCRIPTIONS = [
    'MRtrix3 image header file',
    'MRtrix3 image file',
    'MRtrix3 compressed image file']
"""A description of each MIF file type. """


MIF_DATATYPES = {
    'Bit'        : np.dtype('b1'),
    'Int8'       : np.dtype('b'),
    'UInt8'      : np.dtype('B'),
    'Int16'      : np.dtype('=i2'),
    'UInt16'     : np.dtype('=u2'),
    'Int16LE'    : np.dtype('<i2'),
    'UInt16LE'   : np.dtype('<u2'),
    'Int16BE'    : np.dtype('>i2'),
    'UInt16BE'   : np.dtype('>u2'),
    'Int32'      : np.dtype('=i4'),
    'UInt32'     : np.dtype('=u4'),
    'Int32LE'    : np.dtype('<i4'),
    'UInt32LE'   : np.dtype('<u4'),
    'Int32BE'    : np.dtype('>i4'),
    'UInt32BE'   : np.dtype('>u4'),
    'Float32'    : np.dtype('=f4'),
    'Float32LE'  : np.dtype('<f4'),
    'Float32BE'  : np.dtype('>f4'),
    'Float64'    : np.dtype('=f8'),
    'Float64LE'  : np.dtype('<f8'),
    'Float64BE'  : np.dtype('>f8'),
    'CFloat32'   : np.dtype('=c8'),
    'CFloat32LE' : np.dtype('<c8'),
    'CFloat32BE' : np.dtype('>c8'),
    'CFloat64'   : np.dtype('=c16'),
    'CFloat64LE' : np.dtype('<c16'),
    'CFloat64BE' : np.dtype('>c16'),
}
"""Mappings from MIF datatypes to equivalent numpy dtypes."""


class MIFImage(fslimage.Image):
    """The ``MIFImage`` is an :class:`.Image` sub-class which allows
    loading of MRtrix ``.mif`` image files.
    """

    def __init__(self, filename : str):
        """Load a ``MIFImage`` from ``filename``. """

        header = loadMIFHeader(filename)
        data   = loadMIFImage(filename, header)
        name   = op.basename(filename)
        xform  = createAffine(header)

        super().__init__(data,
                         xform=xform,
                         name=name,
                         dataSource=filename)

        self.__mifHeader = header


    @property
    def mifHeader(self) -> MIFHeader:
        """Return a dict with all key-value pairs contained in the ``.mif``
        image file.
        """
        return dict(self.__mifHeader)


    def save(self, filename=None):
        """Overrides :meth:`.Image.save`.  If a ``filename`` is not provided,
        converts the original (mrtrix) file name into a NIFTI filename, before
        passing it to the :meth:`.Image.save` method.
        """
        if filename is None:
            filename = self.dataSource

        filename = fslimage.removeExt(filename, ALLOWED_EXTENSIONS)

        return fslimage.Image.save(self, filename)


def createAffine(hdr : MIFHeader) -> np.ndarray:
    """Generates a voxel->world affine for the MIF image described by the
    given header.
    """

    # "In MRtrix3, the transform shown always
    # corresponds to the transformation from
    # image coordinates in millimeters to
    # scanner coordinates in millimeters -
    # the voxel size is not taken into
    # account, and the image axes are always
    # normalised to unit amplitude. This may
    # differ from other packages."
    layout = hdr['layoutdir']
    shape  = hdr['dim']
    pixdim = hdr['vox']
    xform  = hdr['transform']

    scale = affine.scaleOffsetXform(pixdim[:3])
    xform = affine.concat(xform, scale)

    flipaxes = []

    if layout[0] == '-': flipaxes.append(0)
    if layout[1] == '-': flipaxes.append(1)
    if layout[2] == '-': flipaxes.append(2)

    if len(flipaxes) > 0:
        xform = affine.flip(shape, xform, *flipaxes)

    return xform


def loadMIFHeader(filename : str) -> MIFHeader:
    """Loads MIF header information from the given file. The key-value
    pairs contained within are returned as a dict.
    """

    header = {}

    if filename.endswith('.gz'): openfunc = gzip.open
    else:                        openfunc = open

    with openfunc(filename, 'rb') as f:

        magic = f.readline().strip()

        if magic != b'mrtrix image':
            raise ValueError(f'{filename} does not look like a mrtrix image file')

        while True:
            line = f.readline().strip()

            if line == b'END':
                break
            if line == b'':
                continue

            line = line.decode('utf-8')

            if not all(c in string.printable for c in line):
                raise ValueError(f'{filename} does not look like a mrtrix image file')

            key, value = line.split(':', maxsplit=1)
            key        = key.strip()
            value      = value.strip()

            if key in header: header[key] = f'{header[key]}\n{value}'
            else:             header[key] = value

    required = ['dim', 'vox', 'layout', 'datatype', 'file']

    for key in required:
        if key not in header:
            raise ValueError(f'{filename} does not look like a mrtrix image file')

    try:
        header['dim']       = [int(v)   for v in header['dim']   .split(',')]
        header['vox']       = [float(v) for v in header['vox']   .split(',')]
        header['layoutdir'] = [v[0]     for v in header['layout'].split(',')]
        header['layout']    = [int(v)   for v in header['layout'].split(',')]
        header['datatype']  = MIF_DATATYPES[header['datatype']]
        header['file']      = header['file'].split()
        header['file']      = (header['file'][0], int(header['file'][1]))

        if 'scaling' in header:
            header['scaling'] = [int(v) for v in header['scaling'].split(',')]

        if 'transform' in header:
            with io.StringIO(header['transform']) as f:
                header['transform'] = np.loadtxt(f, delimiter=',', dtype=np.float32)
                header['transform'] = np.vstack([header['transform'], [0, 0, 0, 1]])

    except Exception as e:
        raise ValueError(f'{filename} does not look like a mrtrix image file') from e

    return header


def loadMIFImage(filename : str, header : MIFHeader) -> np.ndarray:
    """Load MIF image data from the given file.

    :arg filename: Name of file that header was loaded from.
    :arg header:   Dict containing header information.
    :returns:      Numpy array containing the image data.
    """

    shape    = header['dim']
    dtype    = header['datatype']
    layout   = header['layout']
    datafile = header['file'][0]
    offset   = header['file'][1]

    if datafile == '.':
        datafile = filename
    else:
        datafile = op.join(filename.dirname(), datafile)

    if filename.endswith('.gz'): openfunc = gzip.open
    else:                        openfunc = open

    with openfunc(filename, 'rb') as f:
        data = np.fromfile(f, dtype=dtype, offset=offset)

    data = data.reshape(shape, order='F')

    # Make sure first three data
    # dimensions are XYZ
    if len(layout) >= 4:
        dims   = [d for d in layout if d < 3]
        layout = dims + [d for d in layout if d not in dims]
        data   = data.transpose(np.abs(layout))

    return data
