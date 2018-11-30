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
    fsleyesShellHelpText
"""


from __future__ import print_function

import __future__          as futures
import                        os
import os.path             as op
import                        re
import                        sys
import                        types
import                        logging
import                        textwrap
import                        functools
import                        collections

import fsl.utils.settings  as fslsettings
import fsleyes.strings     as strings
import fsleyes.version     as version
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
    from   fsleyes.views.scene3dpanel       import Scene3DPanel
    from   fsleyes.views.timeseriespanel    import TimeSeriesPanel
    from   fsleyes.views.histogrampanel     import HistogramPanel
    from   fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
    from   fsleyes.views.shellpanel         import ShellPanel
    from   fsleyes.actions.screenshot       import screenshot
    from   fsleyes.actions.moviegif         import makeGif
    import fsleyes.state                        as state
    import fsl.data.image                       as fslimage
    import fsl.data.featimage                   as featimage
    import fsl.data.melodicimage                as melimage
    import fsl.data.dtifit                      as dtifit
    import fsl.data.mesh                        as fslmesh
    import fsl.data.vtk                         as fslvtk
    import fsl.data.gifti                       as fslgifti
    import fsl.data.freesurfer                  as fslfs
    import fsl.wrappers                         as wrappers
    import fsl.utils.fslsub                     as fslsub

    def load(filename):
        """Load the specified file into FSLeyes. """

        from . import                 loadoverlay
        import fsleyes.autodisplay as autodisplay

        def onLoad(paths, overlays):

            if len(overlays) == 0:
                return

            overlayList.append(overlays[0])

            if displayCtx.autoDisplay:
                autodisplay.autoDisplay(overlays[0],
                                        overlayList,
                                        displayCtx)

        return loadoverlay.loadOverlays([filename],
                                        onLoad=onLoad,
                                        inmem=displayCtx.loadInMemory,
                                        blocking=True)[0]

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

    def help(obj):
        """Print help on the given object. """
        print(textwrap.dedent(obj.__doc__).strip())


    def getState():
        """Get the current FSLeyes state. """
        return state.getState(frame)


    def setState(s):
        """Set the current FSLeyes state. """
        return state.setState(frame, s)


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
        ('Mesh',               fslmesh.Mesh),
        ('VTKMesh',            fslvtk.VTKMesh),
        ('GiftiMesh',          fslgifti.GiftiMesh),
        ('FreesurferMesh',     fslfs.FreesurferMesh),
        ('OrthoPanel',         OrthoPanel),
        ('LightBoxPanel',      LightBoxPanel),
        ('Scene3DPanel',       Scene3DPanel),
        ('TimeSeriesPanel',    TimeSeriesPanel),
        ('HistogramPanel',     HistogramPanel),
        ('PowerSpectrumPanel', PowerSpectrumPanel),
        ('ShellPanel',         ShellPanel),
        ('overlayList',        overlayList),
        ('displayCtx',         displayCtx),
        ('frame',              frame),
        ('screenshot',         screenshot),
        ('makeGif',            makeGif),
        ('scaledVoxels',       scaledVoxels),
        ('trueScaledVoxels',   trueScaledVoxels),
        ('rawVoxels',          rawVoxels),
        ('setprop',            setprop),
        ('getState',           getState),
        ('setState',           setState),
        ('load',               load),
        ('run',                run),
        ('help',               help),
        ('submit',             fslsub.submit),
        ('info',               fslsub.info),
        ('output',             fslsub.output),
    ))


    # We are assuming that all callable
    # things in the wrappers module
    # are decorated with one of the
    # @fileOrImage or @fileOrArray
    # decorators, found in wrapperutils.
    def loadOutputDecorator(func):
        def wrapper(*args, **kwargs):

            # All wrapper functions return a dict
            # with an attribute called "output".
            result = func(*args, **kwargs)

            # Submitted as a cluster job?
            # The output contains the job ID.
            if 'submit' in kwargs:
                return result.output

            # Called directly? The output
            # contains stdout/stderr.
            stdout, stderr = result.output

            if stdout.strip() != '': print(stdout)
            if stderr.strip() != '': print(stderr, file=sys.stderr)

            # Any image arguments which were
            # specified as LOAD are loaded
            # into FSLeyes.
            for name, val in result.items():
                if isinstance(val, fslimage.Image):
                    overlayList.append(val)
                    displayCtx.getDisplay(val).name = name

            return result

        return functools.update_wrapper(wrapper, func)

    for att in dir(wrappers):
        val = getattr(wrappers, att)
        if att[0] == '_' or isinstance(val, types.ModuleType):
            continue

        if callable(val):
            val = loadOutputDecorator(val)
        _locals[att] = val

    return globals(), _locals


def fsleyesShellHelpText(_globals, _locals):
    """Generates some help text that can be shown at the top of an interactive
    FSLLeyes shell.
    """

    introText = textwrap.dedent("""
    ## FSLeyes {} python shell (Python {})

    Available items:
    """.format(version.__version__, sys.version.split()[0]))

    overrideDocs = {
        'np'   : 'numpy',
        'sp'   : 'scipy',
        'mpl'  : 'matplotlib',
        'plt'  : 'matplotlib.pyplot',
        'LOAD' : 'Load the output from a FSL wrapper function',
    }

    localVars  = list(_locals.keys())
    localDescs = [_locals[k].__doc__
                  if k not in overrideDocs
                  else overrideDocs[k]
                  for k in localVars]

    descWidth   = 60
    varWidth    = max([len(v) for v in localVars])

    localDescs = [d[:descWidth + 30]   for d in localDescs]
    localDescs = [d.replace('\n', ' ') for d in localDescs]
    localDescs = [re.sub(' +', ' ', d) for d in localDescs]
    localDescs = [d[:descWidth]        for d in localDescs]

    shortFmtStr = '  - `{{:{:d}s}}` : {{}}\n'   .format(varWidth)
    longFmtStr  = '  - `{{:{:d}s}}` : {{}}...\n'.format(varWidth)

    for lvar, ldesc in zip(localVars, localDescs):

        if len(ldesc) >= descWidth: fmt = longFmtStr
        else:                       fmt = shortFmtStr

        introText = introText + fmt.format(lvar, ldesc)

    introText = introText + textwrap.dedent("""

    Type help(item) for additional details on a specific item.
    """)

    return introText
