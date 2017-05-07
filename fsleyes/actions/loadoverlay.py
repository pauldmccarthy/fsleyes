#!/usr/bin/env python
#
# loadoverlay.py - Action which allows the user to load overlay files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadOverlayAction`, which allows the user
to load overlay files into the :class:`.OverlayList`.


This module also provides a collection of standalone functions which can be
called directly:

.. autosummary::
   :nosignatures:

   makeWildcard
   loadOverlays
   loadImage
   interactiveLoadOverlays


Finally, this module provides a singleton :class:`RecentPathManager` instance
called :attr:`recentPathManager`, which can be registered with to be notified
when new files have been loaded.
"""


import            logging
import            os
import os.path as op

import numpy   as np

import fsl.utils.async              as async
import fsl.utils.notifier           as notifier
import fsl.utils.settings           as fslsettings
import fsleyes_widgets.utils.status as status
import fsleyes.autodisplay          as autodisplay
import fsleyes.strings              as strings
import fsleyes.overlay              as fsloverlay
from . import                          base


log = logging.getLogger(__name__)


class LoadOverlayAction(base.Action):
    """The ``LoadOverlayAction`` allows the user to add files to the
    :class:`.OverlayList`.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__loadOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __loadOverlay(self):
        """Calls :func:`interactiveLoadOverlays`.

        If overlays were added, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.

        If :attr:`.DisplayContext.autoDisplay` is ``True``, uses the
        :mod:`.autodisplay` module to configure the display properties
        of each new overlay.
        """

        def onLoad(overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)

        interactiveLoadOverlays(onLoad=onLoad,
                                inmem=self.__displayCtx.loadInMemory)


def makeWildcard(allowedExts=None, descs=None):
    """Returns a wildcard string for use in a file dialog, to limit
    the the displayed file types to supported overlay file types.
    """

    import fsl.data.mesh  as fslmesh
    import fsl.data.image as fslimage
    import fsl.data.gifti as fslgifti

    # Hack - the wx wildcard logic doesn't support
    # files with multiple extensions (e.g. .nii.gz).
    # So I'm adding support for '.gz' extensions here.
    if allowedExts is None: allowedExts  = fslimage.ALLOWED_EXTENSIONS     + \
                                           fslmesh .ALLOWED_EXTENSIONS     + \
                                           fslgifti.ALLOWED_EXTENSIONS     + \
                                           ['.gz']
    if descs       is None: descs        = fslimage.EXTENSION_DESCRIPTIONS + \
                                           fslmesh .EXTENSION_DESCRIPTIONS + \
                                           fslgifti.EXTENSION_DESCRIPTIONS + \
                                           ['Compressed images']

    exts  = ['*{}'.format(ext) for ext in allowedExts]
    exts  = [';'.join(exts)]        + exts
    descs = ['All supported files'] + descs

    wcParts = ['|'.join((desc, ext)) for (desc, ext) in zip(descs, exts)]

    return '|'.join(wcParts)


def loadOverlays(paths,
                 loadFunc='default',
                 errorFunc='default',
                 saveDir=True,
                 onLoad=None,
                 inmem=False):
    """Loads all of the overlays specified in the sequence of files
    contained in ``paths``.

    .. note:: The overlays are loaded asynchronously via :func:`.async.idle`.
              Use the ``onLoad`` argument if you wish to be notified when
              the overlays have been loaded.

    :arg loadFunc:  A function which is called just before each overlay
                    is loaded, and is passed the overlay path. The default
                    load function uses the :mod:`.status` module to display
                    the name of the overlay currently being loaded. Pass in
                    ``None`` to disable this default behaviour.

    :arg errorFunc: A function which is called if an error occurs while
                    loading an overlay, being passed the name of the
                    overlay, and either the :class:`Exception` which
                    occurred, or a string containing an error message.  The
                    default function pops up a :class:`wx.MessageBox` with
                    an error message. Pass in ``None`` to disable this
                    default behaviour.

    :arg saveDir:   If ``True`` (the default), the directory of the last
                    overlay in the list of ``paths`` is saved, and used
                    later on as the default load directory.

    :arg onLoad:    Optional function to call when all overlays have been
                    loaded. Must accept one parameter - a list containing
                    the overlays that were loaded.

    :arg inmem:     If ``True``, all :class:`.Image` overlays are
                    force-loaded into memory. Otherwise, large compressed
                    files may be kept on disk. Defaults to ``False``.

    :returns:       A list of overlay objects - just a regular ``list``,
                    not an :class:`OverlayList`.
    """

    import fsl.data.image as fslimage

    # The default load function updates
    # the dialog window created above
    def defaultLoadFunc(s):
        msg = strings.messages['loadOverlays.loading'].format(s)
        status.update(msg)

    # The default error function
    # shows an error dialog
    def defaultErrorFunc(s, e):
        status.reportError(
            strings.titles[  'loadOverlays.error'],
            strings.messages['loadOverlays.error'].format(s),
            e)

    # A function which loads a single overlay
    def loadPath(path):

        loadFunc(path)

        dtype, path = fsloverlay.guessDataSourceType(path)

        if dtype is None:
            errorFunc(path, strings.messages['loadOverlays.unknownType'])
            return

        log.debug('Loading overlay {} (guessed data type: {})'.format(
            path, dtype.__name__))

        try:
            if issubclass(dtype, fslimage.Image):
                overlay = loadImage(dtype, path, inmem=inmem)
            else:
                overlay = dtype(path)

            overlays.append(overlay)

        except Exception as e:
            errorFunc(path, e)

        # Record the path in the
        # recent files list
        recentPathManager.recordPath(path)

    # This function gets called after
    # all overlays have been loaded
    def realOnLoad():

        if saveDir and len(paths) > 0:
            fslsettings.write('loadSaveOverlayDir', op.dirname(paths[-1]))

        if onLoad is not None:
            onLoad(overlays)

    # If loadFunc or errorFunc are explicitly set to
    # None, use these no-op load/error functions
    if loadFunc  is None: loadFunc  = lambda s:    None
    if errorFunc is None: errorFunc = lambda s, e: None

    # Or if not provided, use the
    # default functions defined above
    if loadFunc  == 'default': loadFunc  = defaultLoadFunc
    if errorFunc == 'default': errorFunc = defaultErrorFunc

    overlays = []

    # Load the images
    for path in paths:
        async.idle(loadPath, path)

    async.idle(realOnLoad)


def loadImage(dtype, path, inmem=False):
    """Called by the :func:`loadOverlays` function. Loads an overlay which
    is represented by an ``Image`` instance, or a sub-class of ``Image``.
    Depending upon the image size, the data may be loaded into memory or
    kept on disk, and the initial image data range may be calculated
    from the whole image, or from a sample.

    :arg dtype: Overlay type (``Image``, or a sub-class of ``Image``).
    :arg path:  Path to the overlay file.
    :arg inmem: If ``True``, ``Image`` overlays are loaded into memory.
    """

    rangethres = fslsettings.read('fsleyes.overlay.rangethres', 419430400)
    idxthres   = fslsettings.read('fsleyes.overlay.idxthres',   1073741824)

    # We're going to load the file
    # twice - first to get its
    # dimensions, and then for real.
    #
    # TODO It is annoying that you have to create a 'dtype'
    #      instance twice, as e.g. the MelodicImage does a
    #      bunch of extra stuff (e.g. loading component
    #      time courses) that don't need to be done. Maybe
    #      the path passed to this function could be resolved
    #      (e.g. ./filtered_func.ica/ turned into
    #      ./filtered_func.ica/melodic_IC) so that you can
    #      just create a fsl.data.Image, or a nib.Nifti1Image.
    image = dtype(path,
                  loadData=False,
                  calcRange=False,
                  indexed=False,
                  threaded=False)
    nbytes = np.prod(image.shape) * image.dtype.itemsize
    image  = None

    # If the file is compressed (gzipped),
    # index the file if its compressed size
    # is greater than the index threshold.
    indexed = nbytes > idxthres
    image   = dtype(path,
                    loadData=inmem,
                    calcRange=False,
                    indexed=indexed,
                    threaded=indexed)

    # If the image is bigger than the
    # index threshold, keep it on disk.
    if inmem or (not indexed):
        log.debug('Loading {} into memory'.format(path))
        image.loadData()
    else:
        log.debug('Keeping {} on disk'.format(path))

    # If the image size is less than the range
    # threshold, calculate the full data range
    # now. Otherwise calculate the data range
    # from a sample. This is handled by the
    # Image.calcRange method.
    image.calcRange(rangethres)

    return image


def interactiveLoadOverlays(fromDir=None, dirdlg=False, **kwargs):
    """Convenience function for interactively loading one or more overlays.

    Pops up a file dialog prompting the user to select one or more overlays
    to load.

    :arg fromDir: Directory in which the file dialog should start.  If
                  ``None``, the most recently visited directory (via this
                  function) is used, or a directory from An already loaded
                  overlay, or the current working directory.

    :arg dirdlg:  Use a directory chooser instead of a file dialog.

    :arg kwargs:  Passed  through to the :func:`loadOverlays` function.

    :raise ImportError:  if :mod:`wx` is not present.
    :raise RuntimeError: if a :class:`wx.App` has not been created.
    """
    import wx

    app = wx.GetApp()

    if app is None:
        raise RuntimeError('A wx.App has not been created')

    saveFromDir = False
    if fromDir is None:

        saveFromDir = True
        fromDir     = fslsettings.read('loadSaveOverlayDir')

        if fromDir is None:
            fromDir = os.getcwd()

    if dirdlg:
        msg = strings.titles['interactiveLoadOverlays.dirDialog']
        dlg = wx.DirDialog(app.GetTopWindow(),
                           message=msg,
                           defaultPath=fromDir,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    else:
        msg = strings.titles['interactiveLoadOverlays.fileDialog']
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message=msg,
                            defaultDir=fromDir,
                            wildcard=makeWildcard(),
                            style=wx.FD_OPEN | wx.FD_MULTIPLE)

    if dlg.ShowModal() != wx.ID_OK:
        return []

    if dirdlg: paths = [dlg.GetPath()]
    else:      paths =  dlg.GetPaths()

    dlg.Close()
    dlg.Destroy()

    loadOverlays(paths, saveDir=saveFromDir, **kwargs)


class RecentPathManager(notifier.Notifier):
    """The ``RecentPathManager`` is a simple class which provides
    access to a list of recently loaded files, and can notify
    registered listeners when that list changes. See the
    :attr:`recentPathManager` singleton instance.
    """


    def recordPath(self, path):
        """Adds the given ``path`` to the recent files list. """

        recent = self.listRecentPaths()

        if path in recent:
            return

        recent.append(path)

        if len(recent) > 10:
            recent = recent[-10:]

        recent = op.pathsep.join(recent)

        fslsettings.write('fsleyes.recentFiles', recent)

        self.notify()


    def listRecentPaths(self):
        """Returns a list of recently loaded files. """

        recent = fslsettings.read('fsleyes.recentFiles', None)

        if recent is None: recent = []
        else:              recent = recent.split(op.pathsep)

        return [f for f in recent if op.exists(f)]


recentPathManager = RecentPathManager()
"""A :class:`RecentPathManager` instance which gets updated by the
:func:`loadOverlays` function whenever a new path is loaded. Register
as a listener on this instance if you want to be notified of changes
to the recent paths list.
"""
