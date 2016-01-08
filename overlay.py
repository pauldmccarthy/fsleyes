#!/usr/bin/env python
#
# overlay.py - Defines the OverlayList class, and a few utility functions
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`OverlayList` class, which is a simple but
fundamental class in *FSLeyes* - it is a container for all loaded overlays.
Only one ``OverlayList`` ever exists, and it is shared throughout the entire
application. 


**What is an overlay?**


The definition of an *overlay* is fairly broad; any object can be a added to
the ``OverlayList``  - there is no ``Overlay`` base class, nor any interface
which must be provided by an overlay object. The only requirements imposed on
an overlay type are:

  - Must be able to be created with a single ``__init__`` parameter, which
    is a string specifying the data source location (e.g. a file name).

  - Must have an attribute called ``name``, which is used as the initial
    display name for the overlay.

  - Must have an attribute called ``dataSource``, which is used to identify
    the source of the overlay data.

  - Must be supported by the :mod:`~fsl.fsleyes.gl` package .. ok, this is a
    pretty big requirement .. See the :mod:`.globject` and the
    :data:`.display.OVERLAY_TYPES` documentation for details on how to get
    started with this one.


Currently (``fslpy`` version |version|) the only overlay types in existence
(and able to be rendered) are:

.. autosummary::
   :nosignatures:

   ~fsl.data.image.Image
   ~fsl.data.featimage.FEATImage
   ~fsl.data.melodicimage.MelodicImage
   ~fsl.data.tensorimage.TensorImage
   ~fsl.data.model.Model


A few other utility functions are provided by this module:

.. autosummary::
   :nosignatures:

   guessDataSourceType
   makeWildcard
   loadOverlays
   interactiveLoadOverlays
   saveOverlay
"""

import logging
import os
import os.path as op

import props

import fsl.data.strings   as strings
import fsl.utils.settings as fslsettings
import fsl.utils.status   as status


log = logging.getLogger(__name__)


class OverlayList(props.HasProperties):
    """Class representing a collection of overlays to be displayed together.

    Contains a :class:`props.properties_types.List` property called
    :attr:`overlays`, containing overlay objects (e.g. :class:`.Image`
    or :class:`.Model`objects). Listeners can be registered on the
    ``overlays`` property, so they are notified when the overlay list changes.

    An :class:`OverlayList` object has a few wrapper methods around the
    :attr:`overlays` property, allowing the :class:`OverlayList` to be used as
    if it were a list itself. The :meth:`addOverlays` method is also a
    convenient way to allow the user (i.e. via a GUI) to add overlays to the
    list.
    """


    def __validateOverlay(self, atts, overlay):
        """Makes sure that the given overlay object is valid."""
        return (hasattr(overlay, 'name')      and 
                hasattr(overlay, 'dataSource'))

        
    overlays = props.List(
        listType=props.Object(allowInvalid=False,
                              validateFunc=__validateOverlay))
    """A list of overlay objects to be displayed."""

    
    def __init__(self, overlays=None):
        """Create an ``OverlayList`` object from the given sequence of
        overlays."""
        
        if overlays is None: overlays = []
        self.overlays.extend(overlays)


    def addOverlays(self, fromDir=None, addToEnd=True, dirdlg=False):
        """Convenience method for interactively adding overlays to this
        :class:`OverlayList`.

        :arg fromDir:  Initial directory to show in the dialog - see
                       :func:`interactiveAddOverlays`.

        :arg dirdlg:   Use a directory chooser instead of a file dialog - see
                       :func:`interactiveAddOverlays`.
        
        :arg addToEnd: If ``True`` (the default), the loaded overlays are added
                       to the end of this ``OverlayList``. Otherwise they are
                       added to the beginning.

        :returns:      A list containing the overlays that were added - the 
                       list will be empty if no overlays were added.
        """

        overlays = interactiveLoadOverlays(fromDir=fromDir, dirdlg=dirdlg)

        if len(overlays) > 0:
            if addToEnd: self.extend(      overlays)
            else:        self.insertAll(0, overlays)

        return overlays


    def find(self, name):
        """Returns the first overlay with the given ``name`` or ``dataSource``,
        or ``None`` if there is no overlay with said ``name``/``dataSource``.
        """
        for overlay in self.overlays:
            if overlay.name == name or overlay.dataSource == name:
                return overlay
        return None
            

    # Wrappers around the overlays list property, allowing this
    # OverlayList object to be used as if it is actually a list.
    def __len__(self):
        return self.overlays.__len__()
    
    def __getitem__(self, key):
        return self.overlays.__getitem__(key)
    
    def __iter__(self):
        return self.overlays.__iter__()
    
    def __contains__(self, item):
        return self.overlays.__contains__(item)
    
    def __setitem__(self, key, val):
        return self.overlays.__setitem__(key, val)
    
    def __delitem__(self, key):
        return self.overlays.__delitem__(key)
    
    def index(self, item):
        return self.overlays.index(item)
    
    def count(self, item):
        return self.overlays.count(item)
    
    def append(self, item):
        return self.overlays.append(item)
    
    def extend(self, iterable):
        return self.overlays.extend(iterable)
    
    def pop(self, index=-1):
        return self.overlays.pop(index)
    
    def move(self, from_, to):
        return self.overlays.move(from_, to)
    
    def remove(self, item):
        return self.overlays.remove(item)
    
    def insert(self, index, item):
        return self.overlays.insert(index, item)
    
    def insertAll(self, index, items):
        return self.overlays.insertAll(index, items) 


def guessDataSourceType(path):
    """A convenience function which, given the name of a file or directory,
    figures out a suitable overlay type.

    Returns a tuple containing two values - a type which should be able to
    load the path, and the path itself, possibly adjusted. If the type
    is unrecognised, the first tuple value will be ``None``.
    """

    import fsl.data.image          as fslimage
    import fsl.data.model          as fslmodel
    import fsl.data.featimage      as fslfeatimage
    import fsl.data.melodicimage   as fslmelimage
    import fsl.data.tensorimage    as tensorimage
    import fsl.data.melodicresults as melresults
    import fsl.data.featresults    as featresults

    path = op.abspath(path)

    # VTK files are easy
    if path.endswith('.vtk'):
        return fslmodel.Model, path

    # Analysis directory?
    if op.isdir(path):
        if melresults.isMelodicDir(path):
            return fslmelimage.MelodicImage, path

        elif featresults.isFEATDir(path):
            return fslfeatimage.FEATImage, path

        elif tensorimage.isPathToTensorData(path):
            return tensorimage.TensorImage, path

    # Assume it's a NIFTI image
    try:               path = fslimage.addExt(path, mustExist=True)
    except ValueError: return None, path

    if   melresults.isMelodicImage(path): return fslmelimage.MelodicImage, path
    elif featresults.isFEATImage(  path): return fslfeatimage.FEATImage,   path
    else:                                 return fslimage.Image,           path
        
    # Otherwise, I don't
    # know what to do
    return None, path


def makeWildcard():
    """Returns a wildcard string for use in a file dialog, to limit
    the the displayed file types to supported overlay file types.
    """

    import fsl.data.image as fslimage
    import fsl.data.model as fslmodel
    
    allowedExts  = fslimage.ALLOWED_EXTENSIONS     + \
                   fslmodel.ALLOWED_EXTENSIONS
    descs        = fslimage.EXTENSION_DESCRIPTIONS + \
                   fslmodel.EXTENSION_DESCRIPTIONS

    exts  = ['*{}'.format(ext) for ext in allowedExts]
    exts  = [';'.join(exts)]        + exts
    descs = ['All supported files'] + descs

    wcParts = ['|'.join((desc, ext)) for (desc, ext) in zip(descs, exts)]

    return '|'.join(wcParts)


def loadOverlays(paths, loadFunc='default', errorFunc='default', saveDir=True):
    """Loads all of the overlays specified in the sequence of files
    contained in ``paths``.

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

    :returns:       A list of overlay objects - just a regular ``list``, 
                    not an :class:`OverlayList`.
    """

    defaultLoad = loadFunc == 'default'

    # The default load function updates
    # the dialog window created above
    def defaultLoadFunc(s):
        msg = strings.messages['overlay.loadOverlays.loading'].format(s)
        status.update(msg)

    # The default error function
    # shows an error dialog
    def defaultErrorFunc(s, e):
        import wx
        e     = str(e)
        msg   = strings.messages['overlay.loadOverlays.error'].format(s, e)
        title = strings.titles[  'overlay.loadOverlays.error']
        log.debug('Error loading overlay ({}), ({})'.format(s, e),
                  exc_info=True)
        wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 

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

        loadFunc(path)

        dtype, path = guessDataSourceType(path)

        if dtype is None:
            errorFunc(
                path,
                strings.messages['overlay.loadOverlays.unknownType'])
            continue

        log.debug('Loading overlay {} (guessed data type: {})'.format(
            path, dtype.__name__))
        try:                   overlays.append(dtype(path))
        except Exception as e: errorFunc(path, e)

    if saveDir and len(paths) > 0:
        fslsettings.write('loadOverlayLastDir', op.dirname(paths[-1]))
            
    return overlays


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

    :returns:     A list containing the overlays that were loaded.
    
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
        fromDir     = fslsettings.read('loadOverlayLastDir')
        
        if fromDir is None:
            fromDir = os.getcwd()

    msg = strings.titles['overlay.addOverlays.dialog']

    if dirdlg:
        dlg = wx.DirDialog(app.GetTopWindow(),
                           message=msg,
                           defaultPath=fromDir,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    else:
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message=msg,
                            defaultDir=fromDir,
                            wildcard=makeWildcard(),
                            style=wx.FD_OPEN | wx.FD_MULTIPLE)

    if dlg.ShowModal() != wx.ID_OK:
        return []

    if dirdlg: paths = [dlg.GetPath()]
    else:      paths =  dlg.GetPaths()

    dlg.Destroy()
    del dlg
    
    images = loadOverlays(paths, saveDir=saveFromDir, **kwargs)

    return images
    

def saveOverlay(overlay, fromDir=None):
    """Convenience function for interactively saving changes to an overlay.

    .. note:: Only :class:`.Image` overlays are supported at the moment.

    :param overlay: The overlay instance to be saved.

    :param fromDir: Directory in which the file dialog should start.
                    If ``None``, the most recently visited directory
                    (via this function) is used, or the directory from
                    the given image, or the current working directory.

    :raise ImportError:  if :mod:`wx` is not present.
    :raise RuntimeError: if a :class:`wx.App` has not been created.
    :raise ValueError:   if ``overlay`` is not an :class:`.Image` instance.
    """

    import fsl.data.image as fslimage

    if not isinstance(overlay, fslimage.Image):
        raise ValueError('Only Image overlays are supported')
    
    fslimage.saveImage(overlay, fromDir)
