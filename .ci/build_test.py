import sys
import os
import time
import os.path as op
import numpy as np

from scipy.misc import imread, imsave, imresize
import scipy.ndimage as ndi

import wx

import fsl.utils.idle as idle


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

        img1w, img1h = img1.shape[:2]
        img2w, img2h = img2.shape[:2]

        maxw = max(img1w, img2w)
        maxh = max(img1h, img2h)

        newimg1 = np.zeros((maxw, maxh, 3), dtype=np.uint8)
        newimg2 = np.zeros((maxw, maxh, 3), dtype=np.uint8)

        img1woff = int(round((maxw - img1w) / 2.0))
        img1hoff = int(round((maxh - img1h) / 2.0))
        img2woff = int(round((maxw - img2w) / 2.0))
        img2hoff = int(round((maxh - img2h) / 2.0))

        newimg1[img1woff:img1woff + img1w,
                img1hoff:img1hoff + img1h, :] = img1
        newimg2[img2woff:img2woff + img2w,
                img2hoff:img2hoff + img2h, :] = img2

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


datadir = op.join(os.getcwd(), 'tests', 'testdata')

try:

    # frame.SetSize((int(round(0.9 * 640)), int(round(0.9 * 480))))

    ovl = Image('tests/testdata/3d')
    overlayList.append(ovl)
    ortho = frame.addViewPanel(OrthoPanel)

    ortho.sceneOpts.showLabels = False
    ortho.sceneOpts.showCursor = False

    code = [None]

    def do_test():

        from fsleyes.actions.screenshot import screenshot

        screenshot(ortho, 'file.png')

        benchmark  = op.join(datadir, 'test_screenshot_ortho.png')
        screenshot = imread('file.png')
        benchmark  = imread(benchmark)

        result = compare_images(screenshot, benchmark, 1000)

        if result[0]: code[0] = 0
        else:         code[0] = 1

        print('Image difference: {}'.format(result))

    def set_loc():
        ortho.displayCtx.worldLocation.xyz = [0, -20, 22]

    idle.idle(set_loc, after=2)
    idle.idle(do_test, after=5)

    while code[0] is None:
        wx.Yield()
        time.sleep(0.01)

except Exception as e:
    code[0] = 1

try:
    frame.Close(askLayout=False, askUnsaved=False)
    sys.exit(code[0])
except Exception:
    sys.exit(code[0])
