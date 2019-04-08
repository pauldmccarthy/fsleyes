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

import fsl.utils.idle               as idle
import fsl.utils.notifier           as notifier
import fsl.utils.settings           as fslsettings
import fsl.data.utils               as dutils
import fsleyes_widgets.utils.status as status
import fsleyes.autodisplay          as autodisplay
import fsleyes.strings              as strings
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

        def onLoad(paths, overlays):

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

    import fsl.data.image      as fslimage
    import fsl.data.mghimage   as fslmgh
    import fsl.data.vtk        as fslvtk
    import fsl.data.gifti      as fslgifti
    import fsl.data.freesurfer as fslfs

    # Hack - the wx wildcard logic doesn't support
    # files with multiple extensions (e.g. .nii.gz).
    # So I'm adding support for '.gz' and '.gii'
    # extensions here.
    fsfiles = [op.splitext(f)[1] for f in fslfs.CORE_GEOMETRY_FILES]
    if allowedExts is None:
        allowedExts  = (fslimage.ALLOWED_EXTENSIONS  +
                        fslvtk  .ALLOWED_EXTENSIONS  +
                        fslmgh  .ALLOWED_EXTENSIONS  +
                        fslgifti.ALLOWED_EXTENSIONS  +
                        fsfiles                      +
                        ['.gz', '.gii'])
    if descs is None:
        descs        = (fslimage.EXTENSION_DESCRIPTIONS     +
                        fslvtk  .EXTENSION_DESCRIPTIONS     +
                        fslmgh  .EXTENSION_DESCRIPTIONS     +
                        fslgifti.EXTENSION_DESCRIPTIONS     +
                        fslfs   .CORE_GEOMETRY_DESCRIPTIONS +
                        ['Compressed images', 'GIFTI surfaces'])

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
                 inmem=False,
                 blocking=False):
    """Loads all of the overlays specified in the sequence of files
    contained in ``paths``.

    .. note:: The overlays are loaded asynchronously via :func:`.idle.idle`.
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
                    loaded. Must accept two parameters:

                     - a list of indices, one for each overlay, into the
                       ``paths`` parameter, indicating, for each overlay, the
                       path from which it was loaded.

                     - a list of the overlays that were loaded

    :arg inmem:     If ``True``, all :class:`.Image` overlays are
                    force-loaded into memory. Otherwise, large compressed
                    files may be kept on disk. Defaults to ``False``.

    :arg blocking:  Defaults to ``False``. If ``True``, overlays are loaded
                    immediately (and the ``onLoad`` function is called
                    directly. Otherwise, overlays and the ``onLoad`` are loaded
                    loaded/called on the :func:`.idle.idle` loop.

    :returns:       If ``blocking is False`` (the default), returns ``None``.
                    Otherwise returns a list containing the loaded overlay
                    objects.

    """

    import fsl.data.image as fslimage
    import fsl.data.mesh  as fslmesh

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
    def loadPath(path, idx):

        loadFunc(path)

        dtype, path = dutils.guessType(path)

        if dtype is None:
            errorFunc(path, strings.messages['loadOverlays.unknownType'])
            return

        log.debug('Loading overlay {} (guessed data type: {})'.format(
            path, dtype.__name__))

        try:
            if   issubclass(dtype, fslimage.Image):
                loaded = loadImage(dtype, path, inmem=inmem)
            elif issubclass(dtype, fslmesh.Mesh):
                loaded = [dtype(path, fixWinding=True)]
            else:
                loaded = [dtype(path)]

            overlays.extend(loaded)
            pathIdxs.extend([idx] * len(loaded))

        except Exception as e:
            errorFunc(path, e)

        # Record the path in the
        # recent files list
        recentPathManager.recordPath(path)

    # This function gets called after
    # all overlays have been loaded
    def realOnLoad(*a):

        if saveDir and len(paths) > 0:
            ovlDir = op.abspath(op.dirname(paths[-1]))
            fslsettings.write('loadSaveOverlayDir', ovlDir)

        if onLoad is not None:
            onLoad(pathIdxs, overlays)

    # If loadFunc or errorFunc are explicitly set to
    # None, use these no-op load/error functions
    if loadFunc  is None: loadFunc  = lambda s:    None
    if errorFunc is None: errorFunc = lambda s, e: None

    # Or if not provided, use the
    # default functions defined above
    if loadFunc  == 'default': loadFunc  = defaultLoadFunc
    if errorFunc == 'default': errorFunc = defaultErrorFunc

    pathIdxs = []
    overlays = []
    funcs    = []

    # Load the images
    for idx, path in enumerate(paths):
        funcs.append(lambda p=path, i=idx: loadPath(p, i))
    funcs.append(realOnLoad)

    for func in funcs:
        if blocking: func()
        else:        idle.idle(func)

    if blocking: return overlays
    else:        return None


def loadImage(dtype, path, inmem=False):
    """Called by the :func:`loadOverlays` function. Loads an overlay which
    is represented by an ``Image`` instance, or a sub-class of ``Image``.
    Depending upon the image size, the data may be loaded into memory or
    kept on disk, and the initial image data range may be calculated
    from the whole image, or from a sample.

    This function returns a sequence, most likely containing a single
    :class:`.Image` instance. But in some circumstances (e.g. image files with
    a complex data type), more than one :class:`.Image` will be created and
    returned.

    :arg dtype: Overlay type (``Image``, or a sub-class of ``Image``).
    :arg path:  Path to the overlay file.
    :arg inmem: If ``True``, ``Image`` overlays are loaded into memory.

    :returns:   A sequence of :class:`.Image` instances that were loaded.
    """

    import fsl.data.image as fslimage

    # We're going to load the file
    # twice - first to get its
    # dimensions/data type, and
    # then for real.
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
                  threaded=False)

    imgdtype = image.dtype
    nbytes   = np.prod(image.shape) * image.dtype.itemsize
    image    = None

    # Complex images are split into two separate overlays
    if (dtype is fslimage.Image) and \
       np.issubdtype(imgdtype, np.complexfloating):
        return _loadComplexImage(path)
    else:
        return [_loadNonComplexImage(dtype, path, nbytes, inmem)]


def _loadNonComplexImage(dtype, path, nbytes, inmem):
    """Loads an image with a non-complex data type.

    :arg dtype:  Overlay type - :class:`.Image`, or a sub-class of ``Image``.
    :arg path:   Path to the image file
    :arg nbytes: Number of bytes that the image data takes up.
    :arg inmem:  If ``True``, the file is loaded into memory.
    """

    # If the file is compressed (gzipped),
    # tell the image to use a separate
    # thread for data range calculation.
    #
    # The "idxthres" is so-named because
    # it previously controlled whether
    # gzipped images where kept on disk,
    # and accessed via indexed_gzip. This
    # is now determined automatically for
    # us by nibabel.
    rangethres = fslsettings.read('fsleyes.overlay.rangethres', 419430400)
    idxthres   = fslsettings.read('fsleyes.overlay.idxthres',   1073741824)
    threaded   = nbytes > idxthres
    image      = dtype(path,
                       loadData=inmem,
                       calcRange=False,
                       threaded=threaded)

    # If the image is bigger than the
    # index threshold, keep it on disk.
    if inmem or (not threaded):
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


def _loadComplexImage(path):
    """Loads the specified ``path`` assumed to be a NIFTI image
    with complex data.

    The image is loaded as two separate :class:`.Image` instances,
    containing the real and imaginary components respectively.
    """

    import nibabel        as nib
    import fsl.data.image as fslimage

    image = nib.load(path)
    hdr   = image.header
    data  = image.get_data()

    name  = op.basename(fslimage.removeExt(path))
    rname = '{} [real]'.format(name)
    iname = '{} [imag]'.format(name)

    real = fslimage.Image(np.real(data), name=rname, header=hdr)
    imag = fslimage.Image(np.imag(data), name=iname, header=hdr)

    return real, imag


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
        return

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
