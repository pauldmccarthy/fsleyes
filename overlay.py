#!/usr/bin/env python
#
# overlay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`OverlayList` class, which is a simple but
fundamental class in FSLEyes - it is a container for all displayed overlays.

Only one ``OverlayList`` ever exists, and it is shared throughout the entire
application.
"""

import logging
import os
import os.path as op

import props

import fsl.data.strings   as strings
import fsl.utils.settings as fslsettings


log = logging.getLogger(__name__)


class OverlayList(props.HasProperties):
    """Class representing a collection of overlays to be displayed together.

    Contains a :class:`props.properties_types.List` property called
    ``overlays``, containing overlay objects (e.g. :class:`.Image` or
    :class:`VTKModel`objects).

    An :class:`OverlayList` object has a few wrapper methods around the
    :attr:`overlays` property, allowing the :class:`OverlayList` to be used
    as if it were a list itself.

    There are no restrictions on the type of objects which may be contained
    in the ``OverlayList``, but all objects must have a few attributes:

      - ``name`` ...
    
      - ``dataSource`` ..


    Furthermore, all overlay types must be able to be created with a single
    __init__ parameter, which is a string specifying the data source location
    (e.g. a file).
    """


    def __validateOverlay(self, atts, overlay):
        return (hasattr(overlay, 'name')      and 
                hasattr(overlay, 'dataSource'))

        
    overlays = props.List(
        listType=props.Object(allowInvalid=False,
                              validateFunc=__validateOverlay))
    """A list of overlay objects to be displayed"""

    
    def __init__(self, overlays=None):
        """Create an ``OverlayList`` object from the given sequence of
        overlays."""
        
        if overlays is None: overlays = []
        self.overlays.extend(overlays)


    def addOverlays(self, fromDir=None, addToEnd=True):
        """Convenience method for interactively adding overlays to this
        :class:`OverlayList`.
        """

        overlays = interactiveLoadOverlays(fromDir)
        
        if addToEnd: self.extend(      overlays)
        else:        self.insertAll(0, overlays)


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


def guessDataSourceType(filename):
    """A convenience function which, given the name of a file or directory,
    figures out a suitable data source type.

    Returns a tuple containing two values - a type which should be able to
    load the filename, and the filename, possibly adjusted. If the file type
    is unrecognised, the first tuple value will be ``None``.
    """

    import fsl.data.image       as fslimage
    import fsl.data.model       as fslmodel
    import fsl.data.featimage   as fslfeatimage
    import fsl.data.featresults as featresults

    if filename.endswith('.vtk'):
        return fslmodel.Model, filename

    else:

        if op.isdir(filename):
            if featresults.isFEATDir(filename):
                return fslfeatimage.FEATImage, filename
        else:
        
            filename = fslimage.addExt(filename, False)
            if any([filename.endswith(e)
                    for e in fslimage.ALLOWED_EXTENSIONS]):

                if featresults.isFEATDir(filename):
                    return fslfeatimage.FEATImage, filename
                else:
                    return fslimage.Image, filename

    return None, filename


def makeWildcard():
    """Returns a wildcard string for use in a file dialog, to limit
    the acceptable file types.
    
    :arg allowedExts: A list of strings containing the allowed file
                      extensions.
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

    :param loadFunc:  A function which is called just before each overlay
                      is loaded, and is passed the overlay path. The default
                      load function uses a :mod:`wx` popup frame to display
                      the name of the overlay currently being loaded. Pass in
                      ``None`` to disable this default behaviour.

    :param errorFunc: A function which is called if an error occurs while
                      loading an overlay, being passed the name of the
                      overlay, and either the :class:`Exception` which 
                      occurred, or a string containing an error message.  The
                      default function pops up a :class:`wx.MessageBox` with
                      an error message. Pass in ``None`` to disable this
                      default behaviour.

    :param saveDir:   If ``True`` (the default), the directory of the last
                      overlay in the list of ``paths`` is saved, and used
                      later on as the default load directory.

    :Returns a list of overlay objects
    """

    defaultLoad = loadFunc == 'default'

    # If the default load function is
    # being used, create a dialog window
    # to show the currently loading image
    if defaultLoad:
        import fsl.utils.dialog as fsldlg
        loadDlg = fsldlg.SimpleMessageDialog()

    # The default load function updates
    # the dialog window created above
    def defaultLoadFunc(s):
        msg = strings.messages['overlay.loadOverlays.loading'].format(s)
        loadDlg.SetMessage(msg)

    # The default error function
    # shows an error dialog
    def defaultErrorFunc(s, e):
        import wx
        e     = str(e)
        msg   = strings.messages['overlay.loadOverlays.error'].format(s, e)
        title = strings.titles[  'overlay.loadOverlays.error']
        log.debug('Error loading overlay ({}), ({})'.format(s, e))
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

    # If using the default load 
    # function, show the dialog
    if defaultLoad:
        loadDlg.Show()

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

    if defaultLoad:
        loadDlg.Close()
        loadDlg.Destroy()

    if saveDir and len(paths) > 0:
        fslsettings.write('loadOverlayLastDir', op.dirname(paths[-1]))
            
    return overlays


def interactiveLoadOverlays(fromDir=None, **kwargs):
    """Convenience method for interactively loading one or more overlays.
    
    If the :mod:`wx` package is available, pops up a file dialog
    prompting the user to select one or more overlays to load.

    :param str fromDir:   Directory in which the file dialog should start.
                          If ``None``, the most recently visited directory
                          (via this method) is used, or a directory from
                          an already loaded overlay, or the current working
                          directory.

    Returns: A list containing the overlays that were loaded.
    
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

    dlg = wx.FileDialog(app.GetTopWindow(),
                        message=strings.titles['overlay.addOverlays.dialog'],
                        defaultDir=fromDir,
                        wildcard=makeWildcard(),
                        style=wx.FD_OPEN | wx.FD_MULTIPLE)

    if dlg.ShowModal() != wx.ID_OK:
        return []

    paths  = dlg.GetPaths()

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
                    (via this method) is used, or the directory from
                    the given image, or the current working directory.

    :raise ImportError:  if :mod:`wx` is not present.
    :raise RuntimeError: if a :class:`wx.App` has not been created.
    """

    import fsl.data.image as fslimage

    if not isinstance(overlay, fslimage.Image):
        raise ValueError('Only Image overlays are supported')
    
    fslimage.saveImage(overlay, fromDir)
