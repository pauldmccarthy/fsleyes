#!/usr/bin/env python
#
# reloadoverlay.py - The ReloadOverlayAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ReloadOverlayAction`, a global action
which reloads the currently selected overlay from disk.
"""


import logging
import os.path as op



import fsl.data.image               as fslimage
import fsleyes_widgets.utils.status as status
import fsleyes_props                as props
from . import                          base
from . import                          removeoverlay


log = logging.getLogger(__name__)


class ReloadOverlayAction(base.Action):
    """The ``ReloadOverlayAction`` reloads the currently selected overlay
    from disk. Currently only :class:`.Image` overlays are supported.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``ReloadOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__reloadOverlay)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``ReloadOverlayAction`` is no longer
        required. Removes some property listeners, and calls
        :meth:`.Action.destroy`.
        """
        self.__overlayList.removeListener('overlays',        self.__name)
        self.__displayCtx .removeListener('selectedOverlay', self.__name)

        base.Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the currently selected overlay changes. Enables/disables
        this ``Action`` depending on the type of the newly selected overlay.
        """
        ovl          = self.__displayCtx.getSelectedOverlay()
        self.enabled = (ovl            is not None)    and \
                       (ovl.dataSource is not None)    and \
                       type(ovl) == fslimage.Image     and \
                       op.exists(ovl.dataSource)


    def __reloadOverlay(self):
        """Reloads the currently selected overlay from disk.
        """
        ovl = self.__displayCtx.getSelectedOverlay()

        if ovl is None or type(ovl) != fslimage.Image:
            raise RuntimeError('Only Image overlays can be reloaded')

        index      = self.__overlayList.index(ovl)
        order      = self.__displayCtx.overlayOrder[:]
        dataSource = ovl.dataSource

        status.update('Reloading {}...'.format(dataSource))

        # Get refs to all DisplayContexts -
        # the master one, and the one for
        # every view panel.
        displayCtxs  = [self.__displayCtx]
        viewPanels   = self.__frame.viewPanels
        displayCtxs += [vp.displayCtx for vp in viewPanels]

        # Now get refs to all Display and
        # DisplayOpts instances for this
        # overlay.
        displays = []
        opts     = []

        for dctx in displayCtxs:
            displays.append(self.__displayCtx.getDisplay(ovl))
            opts    .append(self.__displayCtx.getOpts(   ovl))

        # Turn those references into
        # {prop : value} dictionaries
        for i in range(len(displays)):

            d = displays[i]
            o = opts[    i]

            displayProps = d.getAllProperties()[0]
            optProps     = o.getAllProperties()[0]

            displays[i] = {p : getattr(d, p) for p in displayProps}
            opts[    i] = {p : getattr(o, p) for p in optProps}

        # Now that we've got all the settings
        # for this overlay, we'll remove it
        # from the list. If removeOverlay
        # returns False, it probably means
        # the user cancelled the action.
        if not removeoverlay.removeOverlay(self.__overlayList,
                                           self.__displayCtx,
                                           ovl,
                                           'reloadoverlay.unsaved'):
            return

        # Now we re-load the overlay, and add it
        # back in to the list at the same location
        ovl = fslimage.Image(dataSource)
        self.__overlayList.insert(index, ovl)

        # Make sure the overlay is selected,
        # and the display order is preserved
        self.__displayCtx.selectOverlay(ovl)
        self.__displayCtx.overlayOrder = order

        # The last step is to re-apply all of the
        # Display/DisplayOpts settings to the
        # newly created Display/DisplayOpts
        # instances.
        for i, dctx in enumerate(displayCtxs):

            displayProps = displays[i]
            optProps     = opts[    i]
            d            = dctx.getDisplay(ovl)

            for prop, val in displayProps.items():

                try:
                    setattr(d, prop, val)
                except props.DisabledError:
                    continue

            # Get a ref to the DisplayOpts instance
            # after we have configured the Display,
            # as its overlay type may have changed
            # (and hence the DisplayOpts instance
            # may have been re-created).
            o = dctx.getOpts(ovl)
            for prop, val in optProps.items():
                setattr(o, prop, val)

        status.update('{} reloaded.'.format(dataSource))
