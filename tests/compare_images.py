#!/usr/bin/env python
#
# compare_images.py - compare two images
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import sys

import numpy         as np
import scipy.ndimage as ndi

import matplotlib.image as mplimg


def compare_images(img1, img2, threshold):
    """Compares two images using the euclidean distance in RGB space
    between pixels. Returns a tuple containing:

     - A boolean value indicating whether the test passed (the images
       were the same).

     - The sum of the normalised RGB distance between all pixels.
    """

    # Discard alpha values
    img1 = img1[:, :, :3]
    img2 = img2[:, :, :3]

    # pad poth images
    if img1.shape != img2.shape:

        i1w, i1h = img1.shape[:2]
        i2w, i2h = img2.shape[:2]

        maxw = max(i1w, i2w)
        maxh = max(i1h, i2h)

        newimg1 = np.zeros((maxw, maxh, 3), dtype=np.uint8)
        newimg2 = np.zeros((maxw, maxh, 3), dtype=np.uint8)

        i1woff = int(round((maxw - i1w) / 2.0))
        i1hoff = int(round((maxh - i1h) / 2.0))
        i2woff = int(round((maxw - i2w) / 2.0))
        i2hoff = int(round((maxh - i2h) / 2.0))

        newimg1[i1woff:i1woff + i1w,
                i1hoff:i1hoff + i1h, :] = img1
        newimg2[i2woff:i2woff + i2w,
                i2hoff:i2hoff + i2h, :] = img2

        img1 = newimg1
        img2 = newimg2

    img1 = ndi.gaussian_filter(img1, sigma=(2, 2, 0), order=0)
    img2 = ndi.gaussian_filter(img2, sigma=(2, 2, 0), order=0)

    flat1   = img1.reshape(-1, 3)
    flat2   = img2.reshape(-1, 3)

    dist    = np.sqrt(np.sum((flat1 - flat2) ** 2, axis=1))
    dist    = dist.reshape(img1.shape[:2])
    dist    = dist / np.sqrt(3 * 255 * 255)

    ttlDiff = np.sum(dist)

    passed = ttlDiff <= threshold

    return passed, ttlDiff


if __name__ == '__main__':

    argv = sys.argv[1:]
    if len(argv) not in (2, 3):
        print('Usage: compare_images.py image1 image2 [threshold]')
        sys.exit(1)

    image1 = argv[0]
    image2 = argv[1]

    if len(argv) == 2: threshold = 100
    else:              threshold = int(argv[2])

    # TODO use imageio instead of mplimg
    image1 = mplimg.imread(image1) * 255
    image2 = mplimg.imread(image2) * 255

    passed, diff = compare_images(image1, image2, threshold)

    print(diff)

    if passed: sys.exit(0)
    else:      sys.exit(1)
