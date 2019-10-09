#!/usr/bin/env python
#
# saveoverlay.py - Save the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveOverlayAction`, which allows the user
to save the currently selected overlay. A couple of standalone functions are
defined in this module, which do the real work:

.. autosummary::
   :nosignatures:

   saveOverlay
   doSave
   checkOverlaySaveState
"""


import logging

import                                 os
import os.path                      as op

import fsl.utils.settings           as fslsettings
import fsl.data.image               as fslimage
import fsleyes_widgets.utils.status as status
import fsleyes.strings              as strings
from . import                          base


log = logging.getLogger(__name__)


class SaveOverlayAction(base.Action):
    """The ``SaveOverlayAction`` allows the user to save the currently
    selected overlay, if it has been edited, or only exists in memory.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``SaveOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, overlayList, displayCtx, self.__saveOverlay)
        self.__name       = '{}_{}'.format(type(self).__name__, id(self))
        self.__registered = None

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """
        self.displayCtx .removeListener('selectedOverlay', self.__name)
        self.overlayList.removeListener('overlays',        self.__name)

        if self.__registered is not None:
            self.__registered.deregister(self.__name, 'saveState')
            self.__registered = None

        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list changes.

        If the overlay is a :class:`.Image`, and it has unsaved changes,
        this action is enabled; otherwise it is disabled.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        # TODO  Support for other overlay types

        self.enabled = ((overlay is not None)               and
                        isinstance(overlay, fslimage.Image) and
                        (not overlay.saveState))

        if self.__registered is not None:
            self.__registered.deregister(self.__name, 'saveState')
            self.__registered = None

        # Register a listener on the saved property
        # of the currently selected image, so we can
        # enable the save action when the image
        # becomes 'unsaved', and vice versa.
        if self.enabled:
            self.__registered = overlay
            overlay.register(self.__name,
                             self.__overlaySaveStateChanged,
                             'saveState')


    def __overlaySaveStateChanged(self, *a):
        """Called when the :attr:`.Image.saved` property of the currently
        selected overlay changes. Enables/disables this ``SaveOverlayAction``
        accordingly.

        This is only applicable if the current overlay is a :class:`.Image` -
        see the :meth:`__selectedOverlayChanged` method.
        """

        overlay = self.__registered
        self.enabled = (overlay is not None) and (not overlay.saveState)


    def __saveOverlay(self):
        """Called when this :class:`.Action` is executed. Calls
        :func:`saveOverlay` with the currently selected overlay.
        """

        overlay = self.__registered
        if overlay is not None:
            display = self.displayCtx.getDisplay(overlay)
            saveOverlay(overlay, display)


def saveOverlay(overlay, display=None):
    """Saves the currently selected overlay (only if it is a :class:`.Image`),
    by a call to :meth:`.Image.save`. If a ``display`` is provided, the
    :attr:`.Display.name` may be updated to match the new overlay file name.

    :arg overlay: The :class:`.Image` overlay to save
    :arg display: The :class:`.Display` instance associated with the overlay.
    """


    import wx

    # TODO support for other overlay types
    if not isinstance(overlay, fslimage.Image):
        raise RuntimeError('Non-volumetric types not supported yet')

    # If this image has been loaded from a file,
    # ask the user whether they want to overwrite
    # that file, or save the image to a new file.
    #
    if overlay.dataSource is not None:

        # If the data source is not nifti (e.g.
        # mgz), we are not going to overwrite it,
        # so we don't ask.
        if fslimage.looksLikeImage(overlay.dataSource):

            msg   = strings.messages['SaveOverlayAction.overwrite'].format(
                overlay.dataSource)
            title = strings.titles[  'SaveOverlayAction.overwrite'].format(
                overlay.dataSource)

            dlg = wx.MessageDialog(
                wx.GetTopLevelWindows()[0],
                message=msg,
                caption=title,
                style=(wx.ICON_WARNING  |
                       wx.YES_NO        |
                       wx.CANCEL        |
                       wx.NO_DEFAULT))
            dlg.SetYesNoCancelLabels(
                strings.labels['SaveOverlayAction.overwrite'],
                strings.labels['SaveOverlayAction.saveNew'],
                strings.labels['SaveOverlayAction.cancel'])

            response = dlg.ShowModal()

            # Cancel == cancel the save
            # Yes    == overwrite the existing file
            # No     == save to a new file (prompt the user for the file name)
            if response == wx.ID_CANCEL:
                return

            if response == wx.ID_YES:
                doSave(overlay)
                return

        fromDir  = op.dirname(overlay.dataSource)
        filename = fslimage.removeExt(op.basename(overlay.dataSource))
        filename = '{}_copy'.format(filename)
    else:
        fromDir  = fslsettings.read('loadSaveOverlayDir', os.getcwd())

        if display is not None: filename = display.name
        else:                   filename = overlay.name

    filename = filename.replace('/',  '_')
    filename = filename.replace('\\', '_')

    # Ask the user where they
    # want to save the image
    msg = strings.titles['SaveOverlayAction.saveFile']
    dlg = wx.FileDialog(wx.GetApp().GetTopWindow(),
                        message=msg,
                        defaultDir=fromDir,
                        defaultFile=filename,
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

    if dlg.ShowModal() != wx.ID_OK:
        return

    # Make sure that the user chose a supported
    # extension. If not, use the default extension.
    savePath       = dlg.GetPath()
    prefix, suffix = fslimage.splitExt(savePath)

    if suffix == '':
        savePath = '{}{}'.format(prefix, fslimage.defaultExt())

    oldPath = overlay.dataSource
    saveDir = op.dirname(savePath)

    if doSave(overlay, savePath):

        # Cache the save directory for next time.
        fslsettings.write('loadSaveOverlayDir', saveDir)

        # If image was in memory, or its old
        # name equalled the old datasource
        # base name, update its name.
        if oldPath is None or \
           fslimage.removeExt(op.basename(oldPath)) == overlay.name:

            overlay.name = fslimage.removeExt(op.basename(savePath))

            if display is not None:
                display.name = overlay.name


def doSave(overlay, path=None):
    """Called by :func:`saveOverlay`.  Tries to save the given ``overlay`` to
    the given ``path``, and shows an error message if something goes wrong.
    Returns ``True`` if the save was successful, ``False`` otherwise.
    """

    emsg   = strings.messages['SaveOverlayAction.saveError'].format(path)
    etitle = strings.titles[  'SaveOverlayAction.saveError']

    with status.reportIfError(msg=emsg, title=etitle, raiseError=False):
        overlay.save(path)
        return True

    return False


def checkOverlaySaveState(overlayList, displayCtx):
    """Returns ``True`` if all (compatible) overlays are saved to disk,
    ``False`` if there are any overlays with unsaved changes.
    """

    unsaved = []

    for ovl in overlayList:

        # Only Image overlays can be edited/saved
        if not isinstance(ovl, fslimage.Image): continue
        if ovl.saveState:                       continue

        unsaved.append(ovl)

    return len(unsaved) == 0
