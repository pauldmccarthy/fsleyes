import sys
import os
import time
import os.path as op
import numpy as np
import matplotlib.image as mplimg

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

    if img1.shape != img2.shape:
        return False, 0

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

    overlayList.append(Image('tests/testdata/MNI152_T1_2mm_brain'))
    ortho = frame.addViewPanel(OrthoPanel)

    code = [None]

    def do_test():

        from fsleyes.actions.screenshot import screenshot

        screenshot(ortho, 'file.png')

        benchmark  = op.join(datadir, 'test_screenshot_ortho.png')
        screenshot = mplimg.imread('file.png')
        benchmark  = mplimg.imread(benchmark)

        if compare_images(screenshot, benchmark, 50)[0]:
            code[0] = 0
        else:
            code[0] = 1

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
