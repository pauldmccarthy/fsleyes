#!/usr/bin/env python
#
# robustrange.py - The robustRange function
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`robustRange` function, which calculates
the "robust range" range of an :class:`.Image`, as implemented by the
``fslstats -r`` option.
"""

import logging


from fsl.data.image import Image
from fsl.wrappers   import fslstats


log = logging.getLogger(__name__)


def robustRange(image, firstvol=True):
    """Return the robust range of ``image``, as a ``(min, max)`` tuple.

    At the moment, this is done by calling out to ``fslstats``. If ``fslstats``
    cannot be called, the :attr:`.Image.dataRange` is returned.

    :arg image:    The :class:`.Image` object

    :arg firstvol: If ``True`` (default), and the image has more than three
                   dimensions, the range is calculated on the first volume only

    :returns:      A tuple containing the ``(min, max)`` robust range of the
                   image.
    """

    sample = image

    if firstvol and len(image.shape) > 3:
        sample = Image(image[..., 0], header=image.header)

    # pass filename if possible, otherwise
    # fslstats will have to save the image
    # object to disk
    elif image.dataSource is not None:
        sample = image.dataSource

    try:
        return fslstats(sample).r.run()

    except Exception as e:
        log.warning('Could not calculate robust range on %s: %s', image, e)
        return image.dataRange
