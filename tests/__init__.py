#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import            os
import os.path as op
import            gc
import            re
import            sys
import            time
import            shutil
import            logging
import            tempfile
import            traceback
import            contextlib

import            wx

import numpy   as np

from six import StringIO

import matplotlib as mpl
mpl.use('WxAgg')  # noqa

import matplotlib.image as mplimg

import fsleyes_props                as props
import fsl.utils.idle               as idle
import fsl.utils.transform          as transform
import fsl.data.image               as fslimage
import                                 fsleyes
import fsleyes.frame                as fslframe
import fsleyes.main                 as fslmain
import fsleyes.render               as fslrender
import fsleyes.actions.frameactions as frameactions  # noqa
import fsleyes.gl                   as fslgl
import fsleyes.colourmaps           as colourmaps
import fsleyes.displaycontext       as dc
import fsleyes.overlay              as fsloverlay


from .compare_images import compare_images


def haveGL21():
    from fsl.utils.platform import platform as fslplatform
    try:
        return float(fslplatform.glVersion) >= 2.1
    except:
        return False


def haveFSL():
    path = op.expandvars('$FSLDIR/data/standard/MNI152_T1_2mm.nii.gz')
    return op.exists(path)


# Under GTK, a single call to
# yield just doesn't cut it
def realYield(centis=10):
    for i in range(int(centis)):
        wx.YieldIfNeeded()
        time.sleep(0.01)

class CaptureStdout(object):
    """Context manager which captures stdout and stderr. """

    def __init__(self):
        self.reset()

    def reset(self):
        self.__mock_stdout = StringIO('')
        self.__mock_stderr = StringIO('')

    def __enter__(self):
        self.__real_stdout = sys.stdout
        self.__real_stderr = sys.stderr

        sys.stdout = self.__mock_stdout
        sys.stderr = self.__mock_stderr


    def __exit__(self, *args, **kwargs):
        sys.stdout = self.__real_stdout
        sys.stderr = self.__real_stderr

        if args[0] is not None:
            print('Error')
            print('stdout:')
            print(self.stdout)
            print('stderr:')
            print(self.stderr)

        return False

    @property
    def stdout(self):
        self.__mock_stdout.seek(0)
        return self.__mock_stdout.read()

    @property
    def stderr(self):
        self.__mock_stderr.seek(0)
        return self.__mock_stderr.read()


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

    from fsl.utils.platform import platform as fslplatform

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

        # gl already initialised
        if fslplatform.glVersion is not None:
            wx.CallLater(startingDelay, init)
        else:
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



def run_render_test(
        args,
        outfile,
        benchmark,
        size=(640, 480),
        scene='ortho',
        threshold=50):

    glver = os.environ.get('FSLEYES_TEST_GL', '2.1')
    glver = [int(v) for v in glver.split('.')]

    args = '-gl {} {}'.format(*glver) .split() + \
           '-of {}'   .format(outfile).split() + \
           '-sz {} {}'.format(*size)  .split() + \
           '-s  {}'   .format(scene)  .split() + \
           list(args)

    fslrender.main(args)

    # gaaargh, why is macos case insensitive??
    if not op.exists(benchmark):
        benchmark = benchmark.lower()

    testimg  = mplimg.imread(outfile)
    benchimg = mplimg.imread(benchmark)

    result, diff = compare_images(testimg, benchimg, threshold)

    assert result


def run_cli_tests(prefix, tests, extras=None, scene='ortho'):

    if extras is None:
        extras = {}

    glver = os.environ.get('FSLEYES_TEST_GL', '2.1')
    glver = [int(v) for v in glver.split('.')]

    if tuple(glver) < (2, 1):
        exclude = ['tensor', ' sh', '_sh', 'spline', 'mip']
    else:
        exclude = []

    tests     = [t.strip()             for t in tests.split('\n')]
    tests     = [t                     for t in tests if t != '' and t[0] != '#']
    tests     = [re.sub('\s+', ' ', t) for t in tests]
    tests     = [re.sub('#.*', '',  t) for t in tests]
    tests     = [t.strip()             for t in tests]
    allpassed = True

    datadir  = op.join(op.dirname(__file__), 'testdata')
    benchdir = op.join(op.dirname(__file__), 'testdata', 'cli_tests')

    def fill_test(t):
        templates = re.findall('{{(.*?)}}', t)
        for temp in templates:
            t = t.replace('{{' + temp + '}}', eval(temp, {}, extras))
        return t

    with tempdir() as td:

        shutil.copytree(datadir, op.join(td, 'testdata'))
        os.chdir('testdata')

        for test in tests:

            if any([exc in test for exc in exclude]):
                print('CLI test skipped [{}] {}'.format(prefix, test))
                continue

            test      = fill_test(test)
            fname     = test.replace(' ', '_').replace('/', '_')
            fname     = '{}_{}.png'.format(prefix, fname)
            benchmark = op.join(benchdir, fname)
            testfile  = op.join(td, fname)

            try:
                run_render_test(list(test.split()), testfile, benchmark,
                                scene=scene)
                print('CLI test passed [{}] {}'.format(prefix, test))

            except Exception as e:
                allpassed = False
                print('CLI test failed [{}] {}: {}'.format(prefix, test, e))

                if op.exists(testfile):
                    print('Copying {} to {}'.format(testfile, datadir))
                    shutil.copy(testfile, datadir)

    assert allpassed


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




def fliporient(filename):
    base    = fslimage.removeExt(filename)
    outfile = '{}_flipped'.format(base)

    img = fslimage.Image(filename)

    aff       = img.voxToWorldMat
    aff[0, 0] = -aff[0, 0]
    aff[0, 3] =  aff[0, 3] - (img.shape[0] - 1) * img.pixdim[0]

    img.voxToWorldMat = aff
    img[:]            = img[::-1, ...]

    img.save(outfile)
    return outfile



def roi(fname, roi):
    base    = fslimage.removeExt(fname)
    outfile = '{}_roi_{}_{}_{}_{}_{}_{}'.format(base, *roi)

    img = fslimage.Image(fname)
    xs, xe, ys, ye, zs, ze = roi
    data = img[xs:xe, ys:ye, zs:ze, ...]
    img = fslimage.Image(data, header=img.header)

    img.save(outfile)

    return outfile

def discretise(infile, stepsize, min=None, max=None):
    basename = fslimage.removeExt(op.basename(infile))
    img      = fslimage.Image(infile)
    data     = img[:]

    if min is None:
        min = data.min()
    if max is None:
        max = data.max()

    outfile  = '{}_discretised_{}_{}_{}.nii.gz'.format(
        basename, stepsize, min, max)

    for i, li in enumerate(range(min, max, stepsize)):
        data[(data >= li) & (data < (li + stepsize))] = i

    img[:] = data

    img.save(outfile)

    return outfile


def translate(infile, x, y, z):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_translated_{}_{}_{}.nii.gz'.format(basename, x, y, z)
    img      = fslimage.Image(infile)
    xform    = img.voxToWorldMat

    shift             = transform.scaleOffsetXform(1, (x, y, z))
    xform             = transform.concat(shift, xform)
    img.voxToWorldMat = xform

    img.save(outfile)

    return outfile


def rotate(infile, rx, ry, rz):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_rotated_{}_{}_{}.nii.gz'.format(basename, rx, ry, rz)
    img      = fslimage.Image(infile)

    rx = rx * np.pi / 180
    ry = ry * np.pi / 180
    rz = rz * np.pi / 180

    rot               = transform.axisAnglesToRotMat(rx, ry, rz)
    rot               = transform.rotMatToAffine(rot)
    img.voxToWorldMat = transform.concat(rot, img.voxToWorldMat)

    img.save(outfile)

    return outfile


def zero_centre(infile):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_zero_centre.nii.gz'.format(basename)
    img      = fslimage.Image(infile)
    data     = img[:]
    img[:]   = data - data.mean()

    img.save(outfile)

    return outfile
