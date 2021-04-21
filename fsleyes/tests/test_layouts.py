#!/usr/bin/env python
#
# test_layouts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import fsl.data.image as fslimage

import fsleyes.layouts as layouts


from fsleyes.views.orthopanel                   import OrthoPanel
from fsleyes.plugins.controls.atlaspanel        import AtlasPanel
from fsleyes.plugins.controls.lookuptablepanel  import LookupTablePanel
from fsleyes.views.powerspectrumpanel           import PowerSpectrumPanel
from fsleyes.controls.plotlistpanel             import PlotListPanel
from fsleyes.controls.powerspectrumcontrolpanel import PowerSpectrumControlPanel  # noqa

from fsleyes.tests import run_with_fsleyes, realYield


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_layout(frame, overlayList, displayCtx, layout):
    img = fslimage.Image(op.join(datadir, '4d'))
    overlayList.append(img)
    layouts.loadLayout(frame, layout)
    realYield(100)


def test_default():
    run_with_fsleyes(_test_layout, 'default')


def test_ortho():
    run_with_fsleyes(_test_layout, 'ortho')


def test_lightbox():
    run_with_fsleyes(_test_layout, 'lightbox')


def test_3d():
    run_with_fsleyes(_test_layout, '3d')


def test_melodic():
    run_with_fsleyes(_test_layout, 'melodic')


def test_feat():
    run_with_fsleyes(_test_layout, 'feat')




def _test_custom(frame, overlayList, displayCtx):

    ortho = frame.addViewPanel(OrthoPanel,         defaultLayout=False)
    ps    = frame.addViewPanel(PowerSpectrumPanel, defaultLayout=False)

    ortho.togglePanel(AtlasPanel)
    ortho.togglePanel(LookupTablePanel)
    ortho.sceneOpts.showColourBar = True

    ps.togglePanel(PlotListPanel)
    ps.togglePanel(PowerSpectrumControlPanel)

    realYield(50)
    layouts.saveLayout(frame, 'custom_custom')
    frame.removeAllViewPanels()
    realYield(50)

    layouts.loadLayout(frame, 'custom_custom')

    overlayList.append(fslimage.Image(op.join(datadir, '3d')))

    realYield(50)

    ortho, ps = frame.viewPanels

    assert isinstance(ortho, OrthoPanel)
    assert isinstance(ps,    PowerSpectrumPanel)

    orthoctrls = ortho.getPanels()
    psctrls    = ps   .getPanels()

    assert len(orthoctrls) == 2
    assert len(psctrls)    == 2

    assert AtlasPanel                in [type(p) for p in orthoctrls]
    assert LookupTablePanel          in [type(p) for p in orthoctrls]
    assert PlotListPanel             in [type(p) for p in psctrls]
    assert PowerSpectrumControlPanel in [type(p) for p in psctrls]

    assert ortho.sceneOpts.showColourBar
    assert ortho.colourBarCanvas is not None


def test_custom():
    run_with_fsleyes(_test_custom)
