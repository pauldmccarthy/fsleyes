#!/usr/bin/env python
#
# runscript.py - The RunScriptAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RunScriptAction` class, which allows
the user to run a custom Python script.

The following functions are used by the :class:`RunScriptAction`, and are
available for other purposes:

 .. autosummary::
    :nosignatures:

    runScript
    fsleyesScriptEnvironment
"""


from __future__ import print_function

import __future__          as futures
import                        os
import os.path             as op
import                        logging
import                        collections

import fsl.utils.settings  as fslsettings
import fsleyes.strings     as strings
from . import                 base


log = logging.getLogger(__name__)


class RunScriptAction(base.Action):
    """The ``RunScriptAction`` class is an :class:`.Actuion` which allows the
    user to run a custom Python script to control *FSLeyes*. The user is
    prompted to select a script, and then the script is compiled and exceuted.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``RunScriptAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The top-level :class:`.DisplayContext`.
        :arg overlayList: The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__doAction)

        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __doAction(self, script=None):
        """Called when this :class:`.Action` is invoked. If the ``script``
        argument is ``None``, the user is prompted  to select a script file.
        The script is then compiled and executed.
        """

        import wx

        if script is None:

            lastDir = fslsettings.read('runScriptLastDir')

            if lastDir is None:
                lastDir = os.getcwd()

            msg = strings.messages[self, 'runScript']

            # Ask the user what script
            # they want to run
            dlg    = wx.FileDialog(self.__frame,
                                   message=msg,
                                   defaultDir=lastDir,
                                   wildcard='*.py',
                                   style=wx.FD_OPEN)

            if dlg.ShowModal() != wx.ID_OK:
                return

            script = dlg.GetPath()

            # Save the script directory for the
            # next time the user is prompted
            fslsettings.write('runScriptLastDir', op.dirname(script))

        # Run the script, show an
        # error if it crashes
        try:
            runScript(self.__frame,
                      self.__overlayList,
                      self.__displayCtx,
                      script)

        except Exception as e:
            log.warning('Script ({}) could not be executed: {}'.format(
                        script,
                        str(e)),
                        exc_info=True)

            msg = strings.messages[self, 'crash'].format(
                script,
                str(e))

            wx.MessageDialog(self.__frame,
                             message=msg,
                             style=wx.OK | wx.ICON_ERROR).ShowModal()

            return


def runScript(frame, overlayList, displayCtx, script):
    """Compiles and executes the given file, assumed to be a Python script.
    An ``Error`` is raised if the script cannot be compiled or executed.
    """

    # We want scripts to be Python3-like
    flags = (futures.print_function  .compiler_flag |
             futures.absolute_import .compiler_flag |
             futures.division        .compiler_flag |
             futures.unicode_literals.compiler_flag)

    # Is the script a file?
    if op.exists(script):
        with open(script, 'rt') as f:
            log.debug('Loading script {}...'.format(script))
            code = f.read()

    # If not, assume it's
    # a code snippet
    else:
        code = script

    # Compile the script
    log.debug('Compiling {}...'.format(script))
    code = compile(code,
                   script,
                   mode='exec',
                   flags=flags,
                   dont_inherit=True)

    _globals, _locals = fsleyesScriptEnvironment(frame,
                                                 overlayList,
                                                 displayCtx)

    # Workaround http://bugs.python.org/issue991196
    #
    # There is a bug/quirk in the exec function which
    # means that, if you use separate dictionaries for
    # globals and locals, closures won't work. So we
    # copy all locals over to globals, and just use
    # a single dictionary.
    for k, v in _locals.items():
        _globals[k] = v

    # Run the script
    log.debug('Running {}...'.format(script))
    exec(code, _globals)


def fsleyesScriptEnvironment(frame, overlayList, displayCtx):
    """Creates and returns two dictionaries, to be used as the ``globals``
    and ``locals`` dictionaries when executing a custom FSLeyes python
    script.
    """

    import numpy                                as np
    import scipy                                as sp
    import matplotlib                           as mpl
    import matplotlib.pyplot                    as plt
    from   fsleyes.views.orthopanel         import OrthoPanel
    from   fsleyes.views.lightboxpanel      import LightBoxPanel
    from   fsleyes.views.timeseriespanel    import TimeSeriesPanel
    from   fsleyes.views.histogrampanel     import HistogramPanel
    from   fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    from   fsleyes.views.shellpanel         import ShellPanel
    import fsl.data.image                       as fslimage
    import fsl.data.featimage                   as featimage
    import fsl.data.melodicimage                as melimage
    import fsl.data.dtifit                      as dtifit
    import fsl.data.mesh                        as fslmesh
    import fsl.data.gifti                       as fslgifti


    def load(filename):
        """Load the specified file into FSLeyes. """

        from . import                 loadoverlay
        import fsleyes.autodisplay as autodisplay

        def onLoad(overlays):

            if len(overlays) == 0:
                return

            overlayList.append(overlays[0])

            if displayCtx.autoDisplay:
                autodisplay.autoDisplay(overlays[0],
                                        overlayList,
                                        displayCtx)

        loadoverlay.loadOverlays([filename],
                                 onLoad=onLoad,
                                 inmem=displayCtx.loadInMemory)

    def scaledVoxels():
        """Display all NIFTI images in true scaled voxels (but
        with a radiological/neurological flip). """
        for o in overlayList:
            if isinstance(o, fslimage.Nifti):
                displayCtx.getOpts(o).transform = 'pixdim-flip'


    def trueScaledVoxels():
        """Display all NIFTI images in true scaled voxels (without
        any radiological/neurological flip). """
        for o in overlayList:
            if isinstance(o, fslimage.Nifti):
                displayCtx.getOpts(o).transform = 'pixdim'

    def rawVoxels():
        """Display all NIFTI images in raw voxels. """
        for o in overlayList:
            if isinstance(o, fslimage.Nifti):
                displayCtx.getOpts(o).transform = 'id'

    def run(script):
        """Run the specified Python script. """
        runScript(frame, overlayList, displayCtx, script)


    def setprop(substr, propName, value, testName=False):
        """Set the given property value for all overlays which have the
        given ``substr`` in their file path.

        :arg substr:   File path substring.

        :arg propName: Name of the property to change, e.g. ``'cmap'``,
                       ``'alpha'``, etc.

        :arg value:    New property value.

        :arg testName: Defaults to ``False``. If ``True``, the ``substr``
                       is tested against the overlay display name, instead
                       of its file path.
        """

        for ovl in overlayList:

            if ovl.dataSource is not None and substr not in ovl.dataSource:
                continue

            display   = displayCtx.getDisplay(ovl)
            opts      = displayCtx.getOpts(   ovl)
            dispProps = display.getAllProperties()[0]
            optProps  = opts   .getAllProperties()[0]

            if   propName in dispProps: setattr(display, propName, value)
            elif propName in optProps:  setattr(opts,    propName, value)


    _locals = collections.OrderedDict((
        ('np',                 np),
        ('sp',                 sp),
        ('mpl',                mpl),
        ('plt',                plt),
        ('Image',              fslimage.Image),
        ('FEATImage',          featimage.FEATImage),
        ('MelodicImage',       melimage.MelodicImage),
        ('DTIFitTensor',       dtifit.DTIFitTensor),
        ('TriangleMesh',       fslmesh.TriangleMesh),
        ('GiftiSurface',       fslgifti.GiftiSurface),
        ('OrthoPanel',         OrthoPanel),
        ('LightBoxPanel',      LightBoxPanel),
        ('TimeSeriesPanel',    TimeSeriesPanel),
        ('HistogramPanel',     HistogramPanel),
        ('PowerSpectrumPanel', PowerSpectrumPanel),
        ('ShellPanel',         ShellPanel),
        ('overlayList',        overlayList),
        ('displayCtx',         displayCtx),
        ('frame',              frame),
        ('scaledVoxels',       scaledVoxels),
        ('trueScaledVoxels',   trueScaledVoxels),
        ('rawVoxels',          rawVoxels),
        ('setprop',            setprop),
        ('load',               load),
        ('run',                run),
    ))

    return globals(), _locals
