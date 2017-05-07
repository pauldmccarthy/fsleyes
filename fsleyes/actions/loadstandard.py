#!/usr/bin/env python
#
# loadstandard.py - Action which allows the user to open standard images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadStandardAction`, which allows the user
to load in standard space images from the ``$FSLDIR/data/standard/`` directory.
"""


import os.path as op

import fsl.utils.platform as fslplatform
from . import                loadoverlay
from . import                base


class LoadStandardAction(base.Action):
    """The ``LoadStandardAction`` prompts the user to open one or more
    overlays, using ``$FSLDIR/data/standard/`` as the default directory.
    This functionality is provided in the :mod:`.loadoverlay` module.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadStandardAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__loadStandard)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        self.__setStandardDir()

        # If FSLDIR is not set, the setStandardDir
        # disables this action. But we'll listen
        # for changes to FSLDIR, in case it gets
        # set later on.
        fslplatform.platform.register(self.__name, self.__setStandardDir)


    def destroy(self):
        """Must be called when this ``LoadStandardAction`` is no longer
        needed. Performs some clean-up.
        """
        fslplatform.platform.deregister(self.__name)
        base.Action.destroy(self)


    def __setStandardDir(self, *a):
        """Called by :meth:`__init__`, and when the
        :attr:`~fsl.utils.Platform.fsldir` property is changed. Updates
        the path to the FSLDIR standard directory.
        """

        fsldir = fslplatform.platform.fsldir

        if fsldir is not None:
            self.__stddir = op.join(fsldir, 'data', 'standard')
        else:
            self.__stddir = None

        self.enabled = self.__stddir is not None


    def __loadStandard(self):
        """Calls the :func:`.loadoverlay.interactiveLoadOverlays` method.
        If the user added some overlays, updates the
        :attr:`.DisplayContext.selectedOverlay` accordingly.
        """

        def onLoad(overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

        loadoverlay.interactiveLoadOverlays(
            fromDir=self.__stddir,
            onLoad=onLoad,
            inmem=self.__displayCtx.loadInMemory)
