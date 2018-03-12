#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import          os
import          gc
import          time
import          shutil
import          logging
import          tempfile
import          traceback
import          contextlib

import          wx

import matplotlib as mpl
mpl.use('WxAgg')  # noqa

import fsleyes_props                as props
import fsl.utils.idle               as idle
import                                 fsleyes
import fsleyes.frame                as fslframe
import fsleyes.main                 as fslmain
import fsleyes.actions.frameactions as frameactions  # noqa
import fsleyes.gl                   as fslgl
import fsleyes.colourmaps           as colourmaps
import fsleyes.displaycontext       as dc
import fsleyes.overlay              as fsloverlay


from .compare_images import compare_images


# Under GTK, a single call to
# yield just doesn't cut it
def realYield(centis=10):
    for i in range(int(centis)):
        wx.YieldIfNeeded()
        time.sleep(0.01)


@contextlib.contextmanager
def tempdir():
    """Returnsa context manager which creates and returns a temporary
    directory, and then deletes it on exit.
    """

    testdir = tempfile.mkdtemp()
    prevdir = os.getcwd()
    try:

        os.chdir(testdir)
        yield testdir

    finally:
        os.chdir(prevdir)
        shutil.rmtree(testdir)


initialised = [False]

def run_with_fsleyes(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` and run the given function. """

    logging.getLogger().setLevel(logging.WARNING)

    gc.collect()
    idle.idleReset()

    propagateRaise = kwargs.pop('propagateRaise', True)
    startingDelay  = kwargs.pop('startingDelay',  500)
    finishingDelay = kwargs.pop('finishingDelay', 5)
    callAfterApp   = kwargs.pop('callAfterApp',   None)

    result = [None]
    raised = [None]
    frame  = [None]
    app    = [None]
    glver  = os.environ.get('FSLEYES_TEST_GL', '2.1')
    glver  = [int(v) for v in glver.split('.')]

    def init():
        fsleyes.initialise()
        props.initGUI()
        colourmaps.init()
        initialised[0] = True
        fslgl.bootstrap(glver)
        wx.CallAfter(run)

    def finish():
        frame[0].Close(askUnsaved=False, askLayout=False)
        app[0].ExitMainLoop()

    def run():

        overlayList = fsloverlay.OverlayList()
        displayCtx  = dc.DisplayContext(overlayList)
        frame[0]    = fslframe.FSLeyesFrame(None,
                                            overlayList,
                                            displayCtx)

        app[0].SetOverlayListAndDisplayContext(overlayList, displayCtx)
        app[0].SetTopWindow(frame[0])

        frame[0].Show()

        try:
            if func is not None:
                result[0] = func(frame[0],
                                 overlayList,
                                 displayCtx,
                                 *args,
                                 **kwargs)

        except Exception as e:
            traceback.print_exc()
            raised[0] = e

        finally:
            wx.CallLater(finishingDelay, finish)

    app[0] = fslmain.FSLeyesApp()
    dummy  = wx.Frame(None)
    panel  = wx.Panel(dummy)
    sizer  = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(panel, flag=wx.EXPAND, proportion=1)
    dummy.SetSizer(sizer)

    if callAfterApp is not None:
        callAfterApp()

    dummy.SetSize((100, 100))
    dummy.Layout()
    dummy.Show()

    if not initialised[0]:
        wx.CallLater(startingDelay,
                     fslgl.getGLContext,
                     parent=panel,
                     ready=init)
    else:
        wx.CallLater(startingDelay, run)

    app[0].MainLoop()
    dummy.Close()

    time.sleep(1)

    if raised[0] and propagateRaise:
        raise raised[0]

    return result[0]


def run_with_viewpanel(func, vptype, *args, **kwargs):
    def inner(frame, overlayList, displayCtx, *a, **kwa):
        panel = frame.addViewPanel(vptype)
        return func(panel, overlayList, displayCtx, *a, **kwa)
    return run_with_fsleyes(inner, *args, **kwargs)


def run_with_orthopanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with an ``OrthoPanel`` and run the given
    function.
    """
    from fsleyes.views.orthopanel import OrthoPanel
    return run_with_viewpanel(func, OrthoPanel, *args, **kwargs)


def run_with_lightboxpanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with a ``LightBoxPanel`` and run the given
    function.
    """
    from fsleyes.views.lightboxpanel import LightBoxPanel
    return run_with_viewpanel(func, LightBoxPanel, *args, **kwargs)


def run_with_scene3dpanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with a ``Scene3DPanel`` and run the given
    function.
    """
    from fsleyes.views.scene3dpanel import Scene3DPanel
    return run_with_viewpanel(func, Scene3DPanel, *args, **kwargs)


def run_with_timeseriespanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with a ``TimeSeriesPanel`` and run the given
    function.
    """
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    return run_with_viewpanel(func, TimeSeriesPanel, *args, **kwargs)


def run_with_histogrampanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with a ``HistogramPanel`` and run the given
    function.
    """
    from fsleyes.views.histogrampanel import HistogramPanel
    return run_with_viewpanel(func, HistogramPanel, *args, **kwargs)


def run_with_powerspectrumpanel(func, *args, **kwargs):
    """Create a ``FSLeyesFrame`` with a ``PowerSpectrumPanel`` and run the
    given function.
    """
    from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    return run_with_viewpanel(func, PowerSpectrumPanel, *args, **kwargs)
