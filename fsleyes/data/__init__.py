#!/usr/bin/env python
#
# __init__.py - FSLeyes overlay types and data-related utilities.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`fsleyes.data` module contains FSLeyes overlay data types and
some data-related utilities.

Most FSLeyes overlay data types are defined in the ``fslpy`` library
(e.g. :class:`fsl.data.image.Image`, :class:`fsl.data.mesh.Mesh`). This
sub-package provides some additional overlay types that can be displayed with
FSLeyes:

.. autosummary::
   :nosignatures:

   ~fsleyes.data.tractogram.Tractogram
"""

import os.path as op

import fsl.utils.path as fslpath
import fsl.data.utils as dutils


def guessType(path):
    """Wrapper around the :func:`fsl.data.utils.guessType` function from the
    ``fslpy`` library, augmented to support additional data types supported
    by FSLeyes.

    :arg path: Path to a file to be loaded
    :returns:  Tuple containing:

               - A data type which can be used to load the file, or ``None``
                 if the file is not recognised.
               - The file path, possibly modified (e.g. made absolute).
    """

    import fsleyes.data.tractogram as tractogram

    dtype, path = dutils.guessType(path)

    if dtype is not None:
        return dtype, path

    if op.isfile(path):
        if fslpath.hasExt(path.lower(), tractogram.ALLOWED_EXTENSIONS):
            return tractogram.Tractogram, path

    return dtype, path
