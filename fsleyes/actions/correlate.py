#!/usr/bin/env python
#
# correlate.py - The CorrelateAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.PearsonCorrelateAction` and
:class:`PCACorrelateAction` classes, which are :class:`.Action`s that
calculate seed-based correlation on 4D :class:`.Image` overlays.
"""


import threading
import logging

import numpy                  as np
import scipy.spatial.distance as spd

import fsl.data.image               as fslimage
import fsl.utils.async              as async
import fsleyes_props                as props
import fsleyes_widgets.utils.status as fslstatus
import fsleyes.strings              as strings
from . import                          base


log = logging.getLogger(__name__)


class CorrelateAction(base.Action):
    """The ``CorrelateAction`` is a base class for the
    :class:`PearsonCorrelateAction` and :class:`PCACorrelateAction` classes,
    which manages adding/removing correlation overlays to/from the
    :class:`.OverlayList`, and manages execution of the correlation.


    When a 4D :class:`.Image` is selected and the ``CorrelateAction`` is
    invoked, a new 3D :class:`.Image` is created and added to the
    :class:`.OverlayList` - this image is referred to as a *correlate overlay*,
    and is used to store and display the correlation values.
    """

    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``CorrelateAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        base.Action.__init__(self, self.__runCorrelateAction)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        # TODO Use a single data structure -
        #      using two dicts is fragile
        self.__correlateOverlays = {}
        self.__overlayCorrelates = {}

        # The runCorrelateAction cannot be called
        # more than once at a time - this is used
        # as a semaphore to ensure that this is
        # enforced.
        self.__correlateFlag = threading.Event()

        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """

        self.__displayCtx .removeListener('selectedOverlay', self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)
        base.Action.destroy(self)

        self.__correlateOverlays = None
        self.__overlayCorrelates = None


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.

        Enables/disables this action depending on the nature of the selected
        overlay.
        """

        ovl          = self.__displayCtx.getSelectedOverlay()
        isCorrOvl    = ovl in self.__overlayCorrelates

        self.enabled = isCorrOvl or  \
                       ((ovl is not None)               and
                        isinstance(ovl, fslimage.Image) and
                        len(ovl.shape) == 4             and
                        ovl.shape[3] > 1)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Makes sure that
        there are no obsolete correlate overlays in the list, and calls
        :meth:`__selectedOverlayChanged`.
        """
        self.__clearCorrelateOverlays()
        self.__selectedOverlayChanged()


    def __clearCorrelateOverlays(self):
        """Called by :meth:`__overlayListChanged`. Clears internal references
        to any obsolete correlate overlays.
        """

        for overlay, corrOvl in list(self.__correlateOverlays.items()):
            if overlay not in self.__overlayList or \
               corrOvl not in self.__overlayList:
                self.__correlateOverlays.pop(overlay)
                self.__overlayCorrelates.pop(corrOvl)


    def __createCorrelateOverlay(self, overlay, data):
        """Creates a *correlate* overlay for the given ``overlay``, adds
        it to the :class:`.OverlayList`, and initialises some display
        properties.
        """

        display = self.__displayCtx.getDisplay(overlay)
        name    = '{}/correlation'.format(display.name)
        corrOvl = fslimage.Image(data, name=name, header=overlay.header)

        self.__overlayList.append(corrOvl, overlayType='volume')
        self.__correlateOverlays[overlay] = corrOvl
        self.__overlayCorrelates[corrOvl] = overlay

        corrOpts = self.__displayCtx.getOpts(corrOvl)

        with props.suppressAll(corrOpts), \
             props.suppressAll(display):
            corrOpts.cmap              = 'red-yellow'
            corrOpts.negativeCmap      = 'blue-lightblue'
            corrOpts.useNegativeCmap   = True
            corrOpts.displayRange      = [0.05, 1]
            corrOpts.clippingRange.xlo = 0.05

        return corrOvl


    def __runCorrelateAction(self):
        """Called when this :class:`.Action` is invoked. Calculates correlation
        values from the voxel at the current :attr:`.DisplayContext.location`
        (relative to the currently selected overlay) to all other voxels, and
        updates the correlate overlay.

        The correlation calculation and overlay update is performed on a
        separate thread (via :meth:`.async.run`), with a call to
        :meth:`calculateCorrelation`.
        """

        # Because of the multi-threaded/asynchronous
        # way that this function does its job,
        # allowing it to be called multiple times
        # before prior calls have completed would be
        # very dangerous indeed.
        if self.__correlateFlag.is_set():
            log.debug('Correlate action is already '
                      'running - ignoring request')
            return

        # See if a correlate overlay already exists
        # for the currently selected overlay
        ovl     = self.__displayCtx.getSelectedOverlay()
        corrOvl = self.__correlateOverlays.get(ovl, None)

        # If not, check to see if it is a correlate
        # overlay that is selected and, if it is,
        # look up the corresponding source overlay.
        if corrOvl is None:
            if ovl in self.__overlayCorrelates:
                corrOvl = ovl
                ovl     = self.__overlayCorrelates[corrOvl]

        # If corrOvl is still None, it means that
        # there is no correlate overlay for the
        # currently selected overlay. In this case,
        # we'll create a new correlate overlay and
        # add it to the overlay list after the
        # correlation values have been calculated.

        opts = self.__displayCtx.getOpts(ovl)
        xyz  = opts.getVoxel(vround=True)

        if xyz is None:
            return

        data = ovl.nibImage.get_data()

        # The correlation calculation is performed
        # on a separate thread. This thread then
        # schedules a function on async.idle to
        # update the correlation overlay back on the
        # main thread.
        def calcCorr():

            correlations = self.calculateCorrelation(xyz, data)

            # The correlation overlay is updated/
            # created on the main thread.
            def update():

                try:

                    # A correlation overlay already
                    # exists for the source overlay
                    # - update its data
                    if corrOvl is not None:
                        corrOvl[:] = correlations

                    # The correlation overlay hasn't
                    # been created yet - create a
                    # new overlay with the correlation
                    # values.
                    else:
                        self.__createCorrelateOverlay(ovl, correlations)

                finally:
                    fslstatus.clearStatus()
                    self.__correlateFlag.clear()

            async.idle(update)

        # Protect against more calls
        # while this job is running.
        self.__correlateFlag.set()
        fslstatus.update(strings.messages[self, 'calculating'].format(*xyz))
        async.run(calcCorr)


    def calculateCorrelation(self, seed, data):
        """Calculates correlation values between the given ``seed`` voxel (an
        ``(x, y, z)`` tuple) and all other voxels. This method must be
        implemented by sub-classes.

        :arg seed: An ``(x, y, z)`` tuple specifying the seed voxel

        :arg data: A 4D ``numpy`` array containing all of the data.

        :returns:  A 3D ``numpy`` array containing the correlation values.
        """
        raise NotImplementedError('calculateCorrelation must be '
                                  'implemented by sub-classes')


class PearsonCorrelateAction(CorrelateAction):
    """The ``PearsonCorrelateAction`` is a :class:`CorrelateAction` which
    calculates Pearson correlation coefficient values between the seed voxel
    and all other voxels.
    """

    def calculateCorrelation(self, seed, data):
        """Calculates Pearson correlation between the data at the specified
        seed voxel, and all other voxels.
        """

        x, y, z = seed
        npoints = data.shape[3]

        # the scipy.spatial.distance.cdist
        # function can be used to calculate
        # one-to-many correlation values.
        with np.errstate(invalid='ignore'):
            correlations = 1 - spd.cdist(
                data[x, y, z, :].reshape( 1, npoints),
                data            .reshape(-1, npoints),
                metric='correlation')

        # Set any nans to 0
        correlations[np.isnan(correlations)] = 0

        return correlations.reshape(data.shape[:3])


class PCACorrelateAction(CorrelateAction):
    """
    """

    def calculateCorrelation(self, seed, data):
        """
        """

        x, y, z = seed
        nvox    = np.prod(data.shape[:3])
        npoints =         data.shape[ 3]

        correlations = np.dot(data[x, y, z, :].reshape(1,    npoints),
                              data            .reshape(nvox, npoints).T)

        return correlations.reshape(data.shape[:3])
