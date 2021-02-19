#!/usr/bin/env python
#
# volumeopts.py - Defines the VolumeOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VolumeOpts` class."""


import copy
import logging

import numpy as np

import fsl.data.image       as fslimage
import fsleyes_props        as props
import fsleyes.gl           as fslgl

import fsleyes.colourmaps   as fslcm
from . import colourmapopts as cmapopts
from . import volume3dopts  as vol3dopts
from . import                  niftiopts


log = logging.getLogger(__name__)


class VolumeOpts(cmapopts.ColourMapOpts,
                 vol3dopts.Volume3DOpts,
                 niftiopts.NiftiOpts):
    """The ``VolumeOpts`` class defines options for displaying :class:`.Image`
    instances as regular 3D volumes.
    """


    channel = props.Choice(('R', 'G', 'B', 'A'))
    """For images with the NIfTI ``RGB24`` or ``RGBA32`` data type,
    this property controls the channel that gets displayed.
    """


    clipImage = props.Choice()
    """Clip voxels according to the values in another image. By default, voxels
    are clipped by the values in the image itself - this property allows the
    user to choose another image by which voxels are to be clipped. Any image
    which is in the :class:`.OverlayList` can be selected for clipping. The
    :attr:`.ColourMapOpts.clippingRange` property dictates the values outside
    of which voxels are clipped.
    """


    modulateImage = props.Choice()
    """Modulate alapha (opacity) by the intensity of values in the selected
    image, instead of in this image. Only relevant when
    :attr:`.ColourMapOpts.modulateAlpha` is active.
    """


    interpolation = props.Choice(('none', 'linear', 'spline'))
    """How the value shown at a real world location is derived from the
    corresponding data value(s). ``none`` is equivalent to nearest neighbour
    interpolation.
    """


    @classmethod
    def getInitialDisplayRange(cls):
        """This class method returns a tuple containing ``(low, high)``
        percentile values which are used to set the initial values for the
        :attr:`.ColourMapOpts.displayRange` and
        :attr:`.ColourMapOpts.clippingRange` properties. If the initial
        display range has not yet been set (via the
        :meth:`setInitialDisplayRange` method), ``None`` is returned.
        """
        try:
            return cls.__initialDisplayRange
        except AttributeError:
            return None


    @classmethod
    def setInitialDisplayRange(cls, drange):
        """Sets the initial values for the :attr:`.ColourMapOpts.displayRange`
        and :attr:`.ColourMapOpts.clippingRange` to be used for new
        :class:`VolumeOpts` instances.

        :arg drange: A tuple containing ``(low, high)`` display range values
                     as percentiles of the image data range. May be ``None``,
                     in which case the initial display range will be set to the
                     image data range.
        """

        if drange is not None:
            low, high = drange
            if not all((low < high,
                        low >= 0,
                        low <= 100,
                        high >= 0,
                        high <= 100)):
                raise ValueError('Invalid initial display '
                                 'range: {}'.format(drange))

        cls.__initialDisplayRange = drange


    def __init__(self,
                 overlay,
                 display,
                 overlayList,
                 displayCtx,
                 **kwargs):
        """Create a :class:`VolumeOpts` instance for the specified ``overlay``,
        assumed to be an :class:`.Image` instance.

        All arguments are passed through to the :class:`.DisplayOpts`
        constructor.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        # Interpolation cannot be unbound
        # between VolumeOpts instances. This is
        # primarily to reduce memory requirement
        # - if interpolation were different
        # across different views, we would have
        # to create multiple 3D image textures
        # for the same image. Same goes for
        # clip/mod images
        nounbind = kwargs.get('nounbind', [])
        nounbind.append('interpolation')
        nounbind.append('clipImage')
        nounbind.append('modulateImage')
        kwargs['nounbind'] = nounbind

        # Some FSL tools will set the nifti aux_file
        # field to the name of a colour map - Check
        # to see if this is the case (do this before
        # calling __init__, so we don't clobber any
        # existing values).
        cmap = str(overlay.header.get('aux_file', 'none')).lower()

        if cmap == 'mgh-subcortical': cmap = 'subcortical'
        if cmap == 'mgh-cortical':    cmap = 'cortical'

        if cmap in fslcm.getColourMaps():
            self.cmap = cmap

        niftiopts.NiftiOpts.__init__(self,
                                     overlay,
                                     display,
                                     overlayList,
                                     displayCtx,
                                     **kwargs)

        # Some things only happen
        # on the parent instance
        self.__registered = self.getParent() is None

        # Check whether the data range for this
        # image is silly. If it is, and we are
        # on a platform that cannot use floating
        # point textures, we turn on the override
        # data range option.
        if self.__registered and np.issubdtype(overlay.dtype, np.floating):
            import fsleyes.gl.textures.data as texdata
            if not texdata.canUseFloatTextures()[0]:

                dmin, dmax = overlay.dataRange

                # a range of greater than 10e7
                # is defined as being "silly"
                if abs(dmax - dmin) > 10e7:

                    if   overlay.ndim == 3: sample = overlay[:]
                    elif overlay.ndim == 4: sample = overlay[..., 0]

                    drange = np.percentile(sample[sample != 0], [1, 99])

                    self.overrideDataRange       = drange
                    self.enableOverrideDataRange = True

        # Configure the initial display
        # range for new images, from the
        # initialDisplayRange percentiles.
        # We do this before ColourMapOpts.init
        drange = VolumeOpts.getInitialDisplayRange()

        if self.__registered and drange is not None:

            if   overlay.ndim == 3: sample = overlay[:]
            elif overlay.ndim == 4: sample = overlay[..., 0]

            drange = np.percentile(sample[sample != 0], drange)
            crange = [drange[0], overlay.dataRange[1]]

            self.displayRange  = drange
            self.modulateRange = drange
            self.clippingRange = crange

        # If this is not a RGB(A) image, disable
        # the channel property. If it's a RGB
        # image,  remove the "A" option from
        # the channel property.
        if self.__registered:

            nchannels = self.overlay.nvals
            if nchannels == 1:
                self.disableProperty('channel')
            elif nchannels == 3:
                prop = self.getProp('channel')
                prop.removeChoice('A', self)

        cmapopts .ColourMapOpts.__init__(self)
        vol3dopts.Volume3DOpts .__init__(self)

        # Both parent and child VolumeOpts instances
        # listen for Image dataRange changes. The data
        # range for large images may be calculated
        # asynchronously on a separate thread, meaning
        # that data range updates may occur at random
        # times.
        #
        # If parent instances did not listen for data
        # range updates and, at startup, the following
        # sequence of events occurs:
        #
        #   1. Parent VolumeOpts instance created
        #
        #   2. Image.dataRange updated
        #
        #   3. Child VolumeOpts instance created
        #
        # The known parent data range will be 0-0,
        # the child will not receive any notification
        # about the data range change, and the child's
        # data range will be clobbered by the parent's.
        # This ugly situation is avoided simply by
        # having the parent track changes to the data
        # range in addition to all children.
        overlay.register(self.name,
                         self.__dataRangeChanged,
                         'dataRange',
                         runOnIdle=True)

        # We need to listen for changes to clipImage
        # and to [enable]overrideDataRange, as they
        # will change the display data range. These
        # cannot be unbound between parent/children,
        # so only the parent needs to listen.
        if self.__registered:
            overlayList.addListener('overlays',
                                    self.name,
                                    self.__overlayListChanged)
            self       .addListener('clipImage',
                                    self.name,
                                    self.__clipImageChanged)
            self       .addListener('modulateImage',
                                    self.name,
                                    self.__modulateImageChanged)
            self       .addListener('enableOverrideDataRange',
                                    self.name,
                                    self.__enableOverrideDataRangeChanged)
            self       .addListener('overrideDataRange',
                                    self.name,
                                    self.__overrideDataRangeChanged)

            self.__overlayListChanged()
            self.__clipImageChanged(    updateDataRange=False)
            self.__modulateImageChanged(updateDataRange=False)


    def destroy(self):
        """Removes property listeners, and calls the :meth:`NiftiOpts.destroy`
        method.
        """

        overlay     = self.overlay
        overlayList = self.overlayList

        overlay.deregister(self.name, 'dataRange')

        if self.__registered:

            overlayList.removeListener('overlays',                self.name)
            self       .removeListener('clipImage',               self.name)
            self       .removeListener('modulateImage',           self.name)
            self       .removeListener('enableOverrideDataRange', self.name)
            self       .removeListener('overrideDataRange',       self.name)

        cmapopts .ColourMapOpts.destroy(self)
        vol3dopts.Volume3DOpts .destroy(self)
        niftiopts.NiftiOpts    .destroy(self)


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        :attr:`.Image.dataRange` of the image, or the
        :attr:`overrideDataRange` if it is active.
        """
        if self.enableOverrideDataRange: return self.overrideDataRange
        else:                            return self.overlay.dataRange


    def getClippingRange(self):
        """Overrides :meth:`.ColourMapOpts.getClippingRange`.
        If a :attr:`.clipImage` is set, returns its data range. Otherwise
        returns ``None``.
        """

        if self.clipImage is None:
            return cmapopts.ColourMapOpts.getClippingRange(self)
        else:
            return self.clipImage.dataRange


    def getModulateRange(self):
        """Overrides :meth:`.ColourMapOpts.getModulateRange`.
        If a :attr:`.modulateImage` is set, returns its data range. Otherwise
        returns ``None``.
        """

        if self.modulateImage is None:
            return cmapopts.ColourMapOpts.getModulateRange(self)
        else:
            return self.modulateImage.dataRange


    def __dataRangeChanged(self, *a):
        """Called when the :attr:`.Image.dataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange(False, False, False)


    def __enableOverrideDataRangeChanged(self, *a):
        """Called when the :attr:`enableOverrideDataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange()


    def __overrideDataRangeChanged(self, *a):
        """Called when the :attr:`overrideDataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange()


    def __overlayListChanged(self, *a):
        """Called when the :`class:`.OverlayList` changes. Updates the
        options of the :attr:`clipImage` property.
        """

        clipProp = self.getProp('clipImage')
        clipVal  = self.clipImage
        modProp  = self.getProp('modulateImage')
        modVal   = self.modulateImage
        overlays = self.displayCtx.getOrderedOverlays()

        options  = [None]

        for overlay in overlays:

            if overlay is self.overlay:                 continue
            if not isinstance(overlay, fslimage.Image): continue

            options.append(overlay)

        clipProp.setChoices(options, instance=self)
        modProp .setChoices(options, instance=self)

        if clipVal in options: self.clipImage     = clipVal
        else:                  self.clipImage     = None
        if modVal  in options: self.modulateImage = modVal
        else:                  self.modulateImage = None


    def __clipImageChanged(self, *a, **kwa):
        """Called when the :attr:`clipImage` property is changed. Updates
         the range of the :attr:`clippingRange` property.

        :arg updateDataRange: Defaults to ``True``. If ``False``, the
                              :meth:`.ColourMapOpts.updateDataRange` method
                              is not called.
        """

        updateDR = kwa.get('updateDataRange', True)

        haveClipImage = self.clipImage is not None

        if not haveClipImage:
            self.enableProperty('linkLowRanges')
            self.enableProperty('linkHighRanges')

        # If the clipping range is based on another
        # image, it makes no sense to link the low/
        # high display/clipping ranges, as they are
        # probably different. So if a clip image is
        # selected, we disable the link range
        # properties.
        elif self.propertyIsEnabled('linkLowRanges'):

            self.linkLowRanges  = False
            self.linkHighRanges = False

            self.disableProperty('linkLowRanges')
            self.disableProperty('linkHighRanges')

        log.debug('Clip image changed for %s: %s',
                  self.overlay, self.clipImage)

        if updateDR:
            self.updateDataRange(resetDR=False, resetMR=False)


    def __modulateImageChanged(self, *a, **kwa):
        """Called when the :attr:`modulateImage` property is changed. Updates
         the range of the :attr:`modulateRange` property.

        :arg updateDataRange: Defaults to ``True``. If ``False``, the
                              :meth:`.ColourMapOpts.updateDataRange` method
                              is not called.
        """

        updateDR = kwa.get('updateDataRange', True)

        log.debug('Modulate image changed for %s: %s',
                  self.overlay, self.modulateImage)

        if updateDR:
            self.updateDataRange(resetDR=False, resetCR=False)


class VolumeRGBOpts(niftiopts.NiftiOpts):
    """The ``VolumeRGBOpts`` class is intended for displaying
    :class:`.Image` instances containing RGB(A) data.
    """


    rColour = props.Colour(default=(1, 0, 0))
    """Colour to use for the red channel. """


    gColour = props.Colour(default=(0, 1, 0))
    """Colour to use for the green channel. """


    bColour = props.Colour(default=(0, 0, 1))
    """Colour to use for the blue channel. """


    suppressR = props.Boolean(default=False)
    """Suppress the R channel. """


    suppressG = props.Boolean(default=False)
    """Suppress the G channel. """


    suppressB = props.Boolean(default=False)
    """Suppress the B channel. """


    suppressA = props.Boolean(default=False)
    """Suppress the A channel. """


    suppressMode = props.Choice(('white', 'black', 'transparent'))
    """How colours should be suppressed. """


    interpolation = copy.copy(VolumeOpts.interpolation)
    """See :attr:`VolumeOpts.interpolation`. """


    def __init__(self,
                 overlay,
                 display,
                 overlayList,
                 displayCtx,
                 **kwargs):
        """Create a :class:`VolumeRGBOpts` instance for the specified
        ``overlay``, assumed to be an :class:`.Image` instance with type
        ``NIFTI_TYPE_RGB24`` or ``NIFTI_TYPE_RGBA32``.

        All arguments are passed through to the :class:`.DisplayOpts`
        constructor.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        niftiopts.NiftiOpts.__init__(self,
                                     overlay,
                                     display,
                                     overlayList,
                                     displayCtx,
                                     **kwargs)



class ComplexOpts(VolumeOpts):
    """The ``ComplexOpts`` class is a specialisation of :class:`VolumeOpts` for
    images with a complex data type.
    """


    component = props.Choice(('real', 'imag', 'mag', 'phase'))
    """How to display the complex data:

     - ``'real'``   - display the real component
     - ``'imag'```  - display the imaginary component
     - ``'mag'```   - display the magnitude
     - ``'phase'``` - display the phase
    """


    def __init__(self, *args, **kwargs):
        """Create a ``ComplexOpts``. All arguments are passed through to
        the :class:`VolumeOpts` constructor.
        """
        self.__dataRanges = {}
        VolumeOpts.__init__(self, *args, **kwargs)
        self.addListener('component', self.name, self.__componentChanged)


    def destroy(self):
        """Must be called when this ``ComplexOpts`` is no longer needed. """
        VolumeOpts.destroy(self)


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`.
        Calculates and returns the data range of the current
        :attr:`component`.
        """

        drange = self.__dataRanges.get(self.component, None)
        if drange is None:
            data   = self.getComponent(self.overlay[:])
            drange = np.nanmin(data), np.nanmax(data)
            self.__dataRanges[self.component] = drange
        return drange


    def getComponent(self, data):
        """Calculates and returns the current :attr:`component` from the given
        data, assumed to be complex.
        """
        if   self.component == 'real':  return self.getReal(data)
        elif self.component == 'imag':  return self.getImaginary(data)
        elif self.component == 'mag':   return self.getMagnitude(data)
        elif self.component == 'phase': return self.getPhase(data)


    @staticmethod
    def getReal(data):
        """Return the real component of the given complex data. """
        return data.real


    @staticmethod
    def getImaginary(data):
        """Return the imaginary component of the given complex data. """
        return data.imag


    @staticmethod
    def getMagnitude(data):
        """Return the magnitude of the given complex data. """
        return (data.real ** 2 + data.imag ** 2) ** 0.5


    @staticmethod
    def getPhase(data):
        """Return the phase of the given complex data. """
        return np.arctan2(data.imag, data.real)


    def __componentChanged(self, *a):
        """Called when the :attr:`component` changes. Calls
        :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange()
