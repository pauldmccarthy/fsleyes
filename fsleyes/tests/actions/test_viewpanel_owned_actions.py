#!/usr/bin/env python
#
# test_viewpanel_owned_actions.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

from fsl.data.image import Image

from fsleyes.tests import run_with_fsleyes, realYield

from fsleyes.views.orthopanel      import OrthoPanel
from fsleyes.views.timeseriespanel import TimeSeriesPanel


# fsl/fsleyes/fsleyes!480
#
# When a new view panel is opened, the FSLeyesFrame
# destroys and re-creates the Tools menu.

# But Plugin-provided viewpanel tools are "owned" by
# the view panel, and so should not be destroyed.
def test_viewpanel_owned_actions_not_destroyed():
    run_with_fsleyes(_test_viewpanel_owned_actions_not_destroyed)

def _test_viewpanel_owned_actions_not_destroyed(frame, overlayList, displayCtx):

    img = Image(np.random.random((30, 30, 30, 50)))
    overlayList.append(img)
    realYield()

    ortho = frame.addViewPanel(OrthoPanel)
    realYield()

    # Using PearsonCorrelateAction purely for convenience
    ortho.PearsonCorrelateAction()
    realYield()
    assert len(overlayList) == 2

    overlayList.pop(1)
    realYield()

    ts = frame.addViewPanel(TimeSeriesPanel)
    realYield()

    ortho.PearsonCorrelateAction()
    realYield()
    assert len(overlayList) == 2
