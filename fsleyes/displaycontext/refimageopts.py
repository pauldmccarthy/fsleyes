#!/usr/bin/env python
#
# refimageopts.py - The RefImageOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RefImageOpts` class, a mixin for use with
:class:`.DisplayOpts` sub-classes.
"""

import fsl.data.image as fslimage
import fsleyes_props  as props


class RefImageOpts:
    """The ``RefImageOpts`` class is a mixin to be used with
    :class:`.DisplayOpts` sub-classes. It is intended to be used for
    ``DisplayOpts`` class which store settings for overlays that are
    associated with a :class:`.Nifti` image, but are not overlays
    themselves.

    The ``RefImageOpts`` mixin provides a :attr:`refImage` property which
    identifies the reference ``Nifti`` image for the overlay. The ``refImage``
    property can be set to any loaded ``Nifti`` instance.

    See the :class:`.MeshOpts` and :class:`.TractogramOpts` classes for
    examples of ``DisplayOpts`` classes which use the ``RefImageOpts`` mixin.
    """

    refImage = props.Choice()
    """A reference :class:`.Image` instance which the overlay is defined
    in terms of.

    For example, if a :class:`.Mesh` overlay represents the segmentation of
    a sub-cortical region from a T1 image, you would set the ``refImage`` to
    that T1 image.

    Any :class:`.Image` instance in the :class:`.OverlayList` may be chosen
    as the reference image.
    """


    def __init__(self):
        """Initialise a ``RefImageOpts`` instance. This must be called
        *after* the :meth:`.DisplayOpts.__init__` method.
        """

        self.__child = self.getParent() is not None

        if self.__child:
            self.overlayList.listen('overlays',
                                    self.listenerName,
                                    self.__overlayListChanged,
                                    immediate=True)
            self.__overlayListChanged()


    @property
    def referenceImage(self):
        """Overrides :meth:`.DisplayOpts.referenceImage`.

        If a :attr:`refImage` is selected, it is returned. Otherwise,``None``
        is returned.
        """
        return self.refImage


    @property
    def listenerName(self):
        """Returns a unique name for this ``RefImageOpts`` instance, which
        is distinct from its :meth:`.DisplayOpts.name`.
        """
        return f'RefImageOpts_{self.name}'


    def destroy(self):
        """Must be called when this ``RefImageOpts`` is being destroyed.
        De-registers property listeners.
        """
        if self.__child:
            self.overlayList.remove('overlays', self.listenerName)

            for overlay in self.overlayList:
                if not isinstance(overlay, fslimage.Nifti):
                    continue

                # An exception may occur if the
                # DC has been/is being destroyed
                try:
                    display = self.displayCtx.getDIsplay(overlay)
                    display.remove('name', self.listenerName)
                except Exception:
                    pass


    def __overlayListChanged(self):
        """Called when the overlay list changes. Updates the :attr:`refImage`
        property so that it contains a list of overlays which can be
        associated with the mesh.
        """

        imgProp  = self.getProp('refImage')
        imgVal   = self.refImage
        overlays = self.displayCtx.getOrderedOverlays()

        # the overlay for this MeshOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.listenerName)
            return

        imgOptions = [None]

        for overlay in overlays:

            # The overlay must be a Nifti instance.
            if not isinstance(overlay, fslimage.Nifti):
                continue

            imgOptions.append(overlay)

            # Register a listener on the display names so
            # that any bound widgets get updated immediately
            display = self.displayCtx.getDisplay(overlay)
            display.addListener('name',
                                self.listenerName,
                                self.__overlayListChanged,
                                overwrite=True)

        # The previous refImage may have
        # been removed from the overlay list
        if imgVal in imgOptions: self.refImage = imgVal
        else:                    self.refImage = None

        imgProp.setChoices(imgOptions, instance=self)
