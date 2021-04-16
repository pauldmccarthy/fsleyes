#!/usr/bin/env python
#
# timeseries.py - DataSeries classes used by the TimeSeriesPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a number of :class:`.DataSeries` sub-classes which
are use by the :class:`.TimeSeriesPanel`. The following classes are provided:

.. autosummary::
   :nosignatures:

   VoxelTimeSeries
   ComplexTimeSeries
   ImaginaryTimeSeries
   MagnitudeTimeSeries
   PhaseTimeSeries
   FEATTimeSeries
   FEATPartialFitTimeSeries
   FEATEVTimeSeries
   FEATResidualTimeSeries
   FEATModelFitTimeSeries
   MelodicTimeSeries
   MeshTimeSeries
"""


import numpy as np

import fsleyes_props      as props
import fsleyes.strings    as strings
import fsleyes.colourmaps as fslcm
from . import                dataseries


class VoxelTimeSeries(dataseries.VoxelDataSeries):
    """A ``VoxelTimeSeries`` is a ``VoxelDataSeries`` which represents
    time series data.
    """


class ComplexTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` to display time series from 4D
    complex images. The :meth:`getData` method returns the real component
    of the data..


    The :meth:`extraSeries` method returns additional series based on
    the values of the :attr:`plotImaginary`, :attr:`plotMagnitude` and
    :attr:`plotPhase` properties. The :meth:`extraSeries` method will
    return instances of the following classes:

    .. autosummary::
       :nosignatures:

       ImaginaryTimeSeries
       MagnitudeTimeSeries
       PhaseTimeSeries
    """


    plotReal = props.Boolean(default=True)
    """If ``True``, the :meth:`getData` method will return the real
    component time series data.
    """


    plotImaginary = props.Boolean(default=False)
    """If ``True``, the :meth:`extraSeries` method will return an
    :class:`ImaginaryTimeSeries` instance, containing the imaginary
    component data.
    """


    plotMagnitude = props.Boolean(default=False)
    """If ``True``, the :meth:`extraSeries` method will return a
    :class:`MagnitudeTimeSeries` instance, containing the complex
    magnitude.
    """


    plotPhase = props.Boolean(default=False)
    """If ``True``, the :meth:`extraSeries` method will return a
    :class:`PhaseTimeSeries` instance, containing the complex
    phase.
    """


    def __init__(self, overlay, overlayList, displayCtx, plotCanvas):
        """Create a ``ComplexTimeSeries``. All arguments are passed
        through to the :class:`VoxelTimeSeries` constructor.
        """

        VoxelTimeSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)

        self.__imagts = ImaginaryTimeSeries(
            overlay, overlayList, displayCtx, plotCanvas)
        self.__magts = MagnitudeTimeSeries(
            overlay, overlayList, displayCtx, plotCanvas)
        self.__phasets = PhaseTimeSeries(
            overlay, overlayList, displayCtx, plotCanvas)

        for ts in (self.__imagts, self.__magts, self.__phasets):
            ts.colour = fslcm.randomDarkColour()
            ts.bindProps('alpha',     self)
            ts.bindProps('lineWidth', self)
            ts.bindProps('lineStyle', self)


    def makeLabel(self):
        """Returns a string representation of this ``ComplexTimeSeries``
        instance.
        """
        return '{} ({})'.format(VoxelTimeSeries.makeLabel(self),
                                strings.labels[self])


    def getData(self):
        """If :attr:`plotReal` is true, returns the real component
        of the complex data. Otherwise returns ``(None, None)``.
        """
        if not self.plotReal:
            return None, None
        return VoxelTimeSeries.getData(self)


    def extraSeries(self):
        """Returns a list of additional series to be plotted, based
        on the values of the :attr:`plotImaginary`, :attr:`plotMagnitude`
        and :attr:`plotPhase` properties.
        """

        extras = []
        if self.plotImaginary: extras.append(self.__imagts)
        if self.plotMagnitude: extras.append(self.__magts)
        if self.plotPhase:     extras.append(self.__phasets)
        return extras


    def dataAtCurrentVoxel(self):
        """Returns the real component of the data at the current voxel. """
        data = VoxelTimeSeries.dataAtCurrentVoxel(self)
        if data is not None:
            data = data.real
        return data


class ImaginaryTimeSeries(VoxelTimeSeries):
    """An ``ImaginaryTimeSeries`` represents the imaginary component
    of a complex-valued image. ``ImaginaryTimeSeries`` instances
    are created by :class:`ComplexTimeSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this ``ImaginaryTimeSeries``
        instance.
        """
        return '{} ({})'.format(VoxelTimeSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the imaginary component of the data at the current voxel.
        """
        data = VoxelTimeSeries.dataAtCurrentVoxel(self)
        if data is not None:
            data = data.imag
        return data


class MagnitudeTimeSeries(VoxelTimeSeries):
    """An ``MagnitudeTimeSeries`` represents the magnitude of a complex-valued
    image. ``MagnitudeTimeSeries`` instances are created by
    :class:`ComplexTimeSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this ``MagnitudeTimeSeries``
        instance.
        """
        return '{} ({})'.format(VoxelTimeSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the magnitude of the data at the current voxel. """
        data = VoxelTimeSeries.dataAtCurrentVoxel(self)
        if data is not None:
            real = data.real
            imag = data.imag
            data = np.sqrt(real ** 2 + imag ** 2)
        return data


class PhaseTimeSeries(VoxelTimeSeries):
    """An ``PhaseTimeSeries`` represents the phase of a complex-valued
    image. ``PhaseTimeSeries`` instances are created by
    :class:`ComplexTimeSeries` instances.
    """


    def makeLabel(self):
        """Returns a string representation of this ``PhaseTimeSeries``
        instance.
        """
        return '{} ({})'.format(VoxelTimeSeries.makeLabel(self),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the phase of the data at the current voxel. """
        data = VoxelTimeSeries.dataAtCurrentVoxel(self)
        if data is not None:
            real = data.real
            imag = data.imag
            data = np.arctan2(imag, real)
        return data


class FEATTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` class for use with :class:`FEATImage`
    instances, containing some extra FEAT specific options.


    The ``FEATTimeSeries`` class acts as a container for several
    ``TimeSeries`` instances, each of which represent some part of a FEAT
    analysis. The data returned by a call to :meth:`.getData` on a
    ``FEATTimeSeries`` instance returns the fMRI time series data
    (``filtered_func_data`` in the ``.feat`` directory).


    The :meth:`extraSeries` method may be used to retrieve a list of all the
    other ``TimeSeries`` instances which are associated with the
    ``FEATTimeSeries`` instance - all of these ``DataSeries`` instances, in
    addition to this ``FEATTimeSeries`` instasnce, should be plotted.


    For example, if the :attr:`plotData` and :attr:`plotFullModelFit` settings
    are ``True``, the :meth:`extraSeries` method will return a list containing
    one ``TimeSeries`` instance, containing the full model fit, for the voxel
    in question.


    The following classes are used to represent the various parts of a FEAT
    analysis:

    .. autosummary::
       :nosignatures:

       FEATEVTimeSeries
       FEATResidualTimeSeries
       FEATPartialFitTimeSeries
       FEATModelFitTimeSeries
    """


    plotData = props.Boolean(default=True)
    """If ``True``, the FEAT input data is plotted. """


    plotFullModelFit = props.Boolean(default=True)
    """If ``True``, the FEAT full model fit is plotted. """


    plotResiduals = props.Boolean(default=False)
    """If ``True``, the FEAT model residuals are plotted. """


    plotEVs = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the corresponding FEAT EV time course is
    plotted.
    """


    plotPEFits = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the model fit for the corresponding FEAT
    EV is plotted.
    """


    plotCOPEFits = props.List(props.Boolean(default=False))
    """A list of ``Boolean`` properties, one for each EV in the FEAT analysis.
    For elements that are ``True``, the model fit for the corresponding FEAT
    contrast is plotted.
    """


    plotPartial = props.Choice()
    """Plot the raw data, after regression against a chosen EV or contrast.
    The options are populated in the :meth:`__init__` method.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``FEATTimeSeries``.

        All arguments are passed through to the :class:`VoxelTimeSeries`
        constructor.
        """

        VoxelTimeSeries.__init__(self, *args, **kwargs)

        numEVs    = self.overlay.numEVs()
        numCOPEs  = self.overlay.numContrasts()
        copeNames = self.overlay.contrastNames()

        reduceOpts = ['none'] + \
                     ['PE{}'.format(i + 1) for i in range(numEVs)]

        for i in range(numCOPEs):
            name = 'COPE{} ({})'.format(i + 1, copeNames[i])
            reduceOpts.append(name)

        self.getProp('plotPartial').setChoices(reduceOpts, instance=self)

        for i in range(numEVs):
            self.plotPEFits.append(False)
            self.plotEVs   .append(False)

        for i in range(numCOPEs):
            self.plotCOPEFits.append(False)

        self.__fullModelTs =  None
        self.__partialTs   =  None
        self.__resTs       =  None
        self.__evTs        = [None] * numEVs
        self.__peTs        = [None] * numEVs
        self.__copeTs      = [None] * numCOPEs

        if not self.overlay.hasStats():
            self.plotFullModelFit = False

        self.addListener('plotFullModelFit',
                         self.name,
                         self.__plotFullModelFitChanged)
        self.addListener('plotResiduals',
                         self.name,
                         self.__plotResidualsChanged)
        self.addListener('plotPartial',
                         self.name,
                         self.__plotPartialChanged)

        self.addListener('plotEVs',      self.name, self.__plotEVChanged)
        self.addListener('plotPEFits',   self.name, self.__plotPEFitChanged)
        self.addListener('plotCOPEFits', self.name, self.__plotCOPEFitChanged)

        # plotFullModelFit defaults to True, so
        # force the model fit ts creation here
        self.__plotFullModelFitChanged()


    def getData(self):
        """Returns the fMRI time series data at the current voxel. Or,
        if :attr:`plotData` is ``False``, returns ``(None, None)``.
        """
        if not self.plotData:
            return None, None
        return VoxelTimeSeries.getData(self)


    def extraSeries(self):
        """Returns a list containing all of the ``TimeSeries`` instances
        which should be plotted in place of this ``FEATTimeSeries``.
        """

        modelts = []

        if self.plotFullModelFit:      modelts.append(self.__fullModelTs)
        if self.plotResiduals:         modelts.append(self.__resTs)
        if self.plotPartial != 'none': modelts.append(self.__partialTs)

        for i in range(self.overlay.numEVs()):
            if self.plotPEFits[i]:
                modelts.append(self.__peTs[i])

        for i in range(self.overlay.numEVs()):
            if self.plotEVs[i]:
                modelts.append(self.__evTs[i])

        for i in range(self.overlay.numContrasts()):
            if self.plotCOPEFits[i]:
                modelts.append(self.__copeTs[i])

        return modelts


    def __getContrast(self, fitType, idx):
        """Returns a contrast vector for the given model fit type, and index.

        :arg fitType: either ``'full'``, ``'pe'``, or ``'cope'``. If
                      ``'full'``, the ``idx`` argument is ignored.

        :arg idx:     The EV or contrast index for ``'pe'`` or ``'cope'`` model
                      fits.
        """

        if fitType == 'full':
            return [1] * self.overlay.numEVs()
        elif fitType == 'pe':
            con      = [0] * self.overlay.numEVs()
            con[idx] = 1
            return con
        elif fitType == 'cope':
            return self.overlay.contrasts()[idx]


    def __createModelTs(self, tsType, *args, **kwargs):
        """Creates a ``TimeSeries`` instance of the given ``tsType``, and
        sets its display settings  according to those of this
        ``FEATTimeSeries``.

        :arg tsType: The type to create, e.g. :class:`FEATModelFitTimeSeries`,
                     :class:`FEATEVTimeSeries`, etc.

        :arg args:   Passed to the ``tsType`` constructor.

        :arg kwargs: Passed to the ``tsType`` constructor.
        """

        ts = tsType(self.overlay,
                    self.overlayList,
                    self.displayCtx,
                    self.plotCanvas,
                    self,
                    *args,
                    **kwargs)

        ts.alpha     = self.alpha
        ts.lineWidth = self.lineWidth
        ts.lineStyle = self.lineStyle

        if isinstance(ts, FEATModelFitTimeSeries) and ts.fitType == 'full':
            ts.colour = (0, 0, 0.8)
        else:
            ts.colour = fslcm.randomDarkColour()

        return ts


    def __plotPartialChanged(self, *a):
        """Called when the :attr:`plotPartial` setting changes.

        If necessary, creates and caches a :class:`FEATPartialFitTimeSeries`
        instance.
        """

        partial = self.plotPartial

        if partial == 'none' and self.__partialTs is not None:
            self.__partialTs = None
            return

        partial = partial.split()[0]

        # fitType is either 'cope' or 'pe'
        fitType = partial[:-1].lower()
        idx     = int(partial[-1]) - 1

        self.__partialTs = self.__createModelTs(
            FEATPartialFitTimeSeries,
            self.__getContrast(fitType, idx),
            fitType,
            idx)


    def __plotResidualsChanged(self, *a):
        """Called when the :attr:`plotResiduals` setting changes.

        If necessary, creates and caches a :class:`FEATResidualTimeSeries`
        instance.
        """

        if not self.plotResiduals:
            self.__resTs = None
            return

        self.__resTs = self.__createModelTs(FEATResidualTimeSeries)


    def __plotEVChanged(self, *a):
        """Called when the :attr:`plotEVs` setting changes.

        If necessary, creates and caches one or more :class:`FEATEVTimeSeries`
        instances.
        """

        for evnum, plotEV in enumerate(self.plotEVs):

            if not self.plotEVs[evnum]:
                self.__evTs[evnum] = None

            elif self.__evTs[evnum] is None:
                self.__evTs[evnum] = self.__createModelTs(
                    FEATEVTimeSeries, evnum)


    def __plotCOPEFitChanged(self, *a):
        """Called when the :attr:`plotCOPEFits` setting changes.

        If necessary, creates and caches one or more
        :class:`FEATModelFitTimeSeries` instances.
        """

        for copenum, plotCOPE in enumerate(self.plotCOPEFits):

            if not self.plotCOPEFits[copenum]:
                self.__copeTs[copenum] = None

            elif self.__copeTs[copenum] is None:
                self.__copeTs[copenum] = self.__createModelTs(
                    FEATModelFitTimeSeries,
                    self.__getContrast('cope', copenum),
                    'cope',
                    copenum)


    def __plotPEFitChanged(self, *a):
        """Called when the :attr:`plotPEFits` setting changes.

        If necessary, creates and caches one or more
        :class:`FEATModelFitTimeSeries` instances.
        """

        for evnum, plotPE in enumerate(self.plotPEFits):

            if not self.plotPEFits[evnum]:
                self.__peTs[evnum] = None

            elif self.__peTs[evnum] is None:
                self.__peTs[evnum] = self.__createModelTs(
                    FEATModelFitTimeSeries,
                    self.__getContrast('pe', evnum),
                    'pe',
                    evnum)


    def __plotFullModelFitChanged(self, *a):
        """Called when the :attr:`plotFullModelFit` setting changes.

        If necessary, creates and caches a
        :class:`FEATModelFitTimeSeries` instance.
        """

        if not self.plotFullModelFit:
            self.__fullModelTs = None
            return

        self.__fullModelTs = self.__createModelTs(
            FEATModelFitTimeSeries, self.__getContrast('full', -1), 'full', -1)


class FEATPartialFitTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` class which represents the partial model
    fit of an EV or contrast from a FEAT analysis at a specific voxel.
    Instances of this class are created by the :class:`FEATTimeSeries` class.
    """
    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 plotCanvas,
                 parentTs,
                 contrast,
                 fitType,
                 idx):
        """Create a ``FEATPartialFitTimeSeries``.

        :arg overlay:     The :class:`.FEATImage` instance to extract the data
                          from.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``FEATPartialFitTimeSeries``.

        :arg parentTs:    The :class:`.FEATTimeSeries` instance that has
                          created this ``FEATPartialFitTimeSeries``.

        :arg contrast:    The contrast vector to calculate the partial model
                          fit for.

        :arg fitType:     The model fit type, either ``'full'``, ``'pe'`` or
                          ``'cope'``.

        :arg idx:         If the model fit type is ``'pe'`` or ``'cope'``,
                          the EV/contrast index.
        """
        VoxelTimeSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)

        self.parentTs = parentTs
        self.contrast = contrast
        self.fitType  = fitType
        self.idx      = idx


    def dataAtCurrentVoxel(self):
        """Returns the partial model fit for the voxel and model fit type
        specified in the constructop.

        See the :meth:`.FEATImage.partialFit` method.
        """
        opts   = self.displayCtx.getOpts(self.overlay)
        coords = opts.getVoxel()

        if coords is None:
            return None

        return self.overlay.partialFit(self.contrast, coords)


class FEATEVTimeSeries(dataseries.DataSeries):
    """A :class:`TimeSeries` class which represents the time course of an
    EV from a FEAT analysis. Instances of this class are created by the
    :class:`FEATTimeSeries` class.
    """

    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 plotCanvas,
                 parentTs,
                 idx):
        """Create a ``FEATEVTimeSeries``.

        :arg overlay:     The :class:`.FEATImage` instance to extract the data
                          from.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``FEATEVTimeSeries``.

        :arg parentTs:    The :class:`.FEATTimeSeries` instance that has
                          created this ``FEATEVTimeSeries``.

        :arg idx:         The EV index.
        """
        dataseries.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)

        self.parentTs = parentTs
        self.idx      = idx


    def makeLabel(self):
        """Returns a string representation of this ``FEATEVTimeSeries``
        instance.
        """

        display = self.displayCtx.getDisplay(self.overlay)

        return '{} EV{} ({})'.format(
            display.name,
            self.idx + 1,
            self.overlay.evNames()[self.idx])


    def getData(self):
        """Returns the time course of the EV specified in the constructor. """

        opts   = self.displayCtx.getOpts(self.overlay)
        coords = opts.getVoxel()
        design = self.overlay.getDesign(coords)
        ydata  = design[:, self.idx]
        xdata  = np.arange(len(ydata))

        return xdata, ydata


class FEATResidualTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` class which represents the time course of
    the residuals from a FEAT analysis at a specific voxel. Instances of this
    class are created by the :class:`FEATTimeSeries` class.
    """

    def __init__(self, overlay, overlayList, displayCtx, plotCanvas, parentTs):
        """Create a ``FEATResidualTimeSeries``.

        :arg overlay:     The :class:`.FEATImage` instance to extract the data
                          from.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``FEATResidualTimeSeries``.

        :arg parentTs:    The :class:`.FEATTimeSeries` instance that has
                          created this ``FEATResidualTimeSeries``.
        """
        VoxelTimeSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)
        self.parentTs = parentTs


    def makeLabel(self):
        """Returns a string representation of this ``FEATResidualTimeSeries``
        instance.
        """
        return '{} ({})'.format(self.parentTs.makeLabel(),
                                strings.labels[self])


    def dataAtCurrentVoxel(self):
        """Returns the residuals for the current voxel. """

        opts  = self.displayCtx.getOpts(self.overlay)
        voxel = opts.getVoxel()

        if voxel is None:
            return None

        x, y, z = voxel
        data    = self.overlay.getResiduals()[x, y, z, :]

        return data


class FEATModelFitTimeSeries(VoxelTimeSeries):
    """A :class:`TimeSeries` class which represents the time course for
    a model fit from a FEAT analysis at a specific voxel. Instances of this
    class are created by the :class:`FEATTimeSeries` class.
    """

    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 plotCanvas,
                 parentTs,
                 contrast,
                 fitType,
                 idx):
        """Create a ``FEATModelFitTimeSeries``.

        :arg overlay:     The :class:`.FEATImage` instance to extract the data
                          from.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``FEATModelFitTimeSeries``.

        :arg parentTs:    The :class:`.FEATTimeSeries` instance that has
                          created this ``FEATModelFitTimeSeries``.

        :arg contrast:    The contrast vector to calculate the partial model
                          fit for.

        :arg fitType:     The model fit type, either ``'full'``, ``'pe'`` or
                          ``'cope'``.

        :arg idx:         If the model fit type is ``'pe'`` or ``'cope'``,
        """

        if fitType not in ('full', 'cope', 'pe'):
            raise ValueError('Unknown model fit type {}'.format(fitType))

        VoxelTimeSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)
        self.parentTs = parentTs
        self.fitType  = fitType
        self.idx      = idx
        self.contrast = contrast


    def makeLabel(self):
        """Returns a string representation of this ``FEATModelFitTimeSeries``
        instance.
        """

        label = '{} ({})'.format(
            self.parentTs.makeLabel(),
            strings.labels[self, self.fitType])

        if self.fitType == 'full':
            return label

        elif self.fitType == 'cope':
            return label.format(
                self.idx + 1,
                self.overlay.contrastNames()[self.idx])

        elif self.fitType == 'pe':
            return label.format(self.idx + 1)


    def dataAtCurrentVoxel(self):
        """Returns the FEAT model fit at the current voxel. """

        opts     = self.displayCtx.getOpts(self.overlay)
        voxel    = opts.getVoxel()
        contrast = self.contrast

        if voxel is None:
            return None

        return self.overlay.fit(contrast, voxel)


class MelodicTimeSeries(dataseries.DataSeries):
    """A :class:`.DataSeries` class which encapsulates the time course for
    one component of a :class:`.MelodicImage`. The :meth:`getData` method
    returns the time course of the component specified by the current
    :class:`.NiftiOpts.volume`.
    """

    def __init__(self, overlay, overlayList, displayCtx, plotCanvas):
        """Create a ``MelodicTimeSeries``.

        :arg overlay:     A :class:`.MelodicImage` overlay.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``MelodicTimeSeries``.
        """
        dataseries.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)


    def getComponent(self):
        """Returns the index (starting from 0) of the current Melodic
        component, as dictated by the :class:`.NiftiOpts.volume` property.
        """
        opts = self.displayCtx.getOpts(self.overlay)
        return opts.volume


    def makeLabel(self):
        """Returns a string representation of this ``MelodicTimeSeries``. """

        display = self.displayCtx.getDisplay(self.overlay)
        return '{} [component {}]'.format(display.name,
                                          self.getComponent() + 1)


    def getData(self):
        """Returns the time course of the current Melodic component. """

        component = self.getComponent()
        ydata     = self.overlay.getComponentTimeSeries(component)
        xdata     = np.arange(len(ydata))
        return xdata, ydata


class MeshTimeSeries(dataseries.DataSeries):
    """A ``MeshTimeSeries`` object encapsulates the time course for a
    :class:`.Mesh` overlay which has some time series vertex data
    associated with it. See the :attr:`.MeshOpts.vertexData` property.
    """


    def __init__(self, overlay, overlayList, displayCtx, plotCanvas):
        """Create a ``MeshTimeSeries`` instance.

        :arg overlay:     The :class:`.Mesh` instance to extract the data from.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotCanvas:   The :class:`TimeSeriesPanel` which owns this
                          ``TimeSeries``.
        """
        dataseries.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)


    def makeLabel(self):
        """Returns a label to use for this ``MeshTimeSeries`` on the
        legend.
        """

        display = self.displayCtx.getDisplay(self.overlay)

        if self.__haveData():

            opts    = display.opts
            vidx    = opts.getVertex()

            return '{} [{}]'.format(display.name, vidx)

        else:
            return display.name


    def __haveData(self):
        """Returns ``True`` if there is currently time series data to show
        for this ``MeshTimeSeries``, ``False`` otherwise.
        """
        opts = self.displayCtx.getOpts(self.overlay)
        vidx = opts.getVertex()
        vd   = opts.getVertexData()

        return vidx is not None and vd is not None and vd.shape[1] > 1


    def getData(self):
        """Returns the data at the current location for the
        :class:`.Mesh`, or ``(None, None)`` if there is no data.
        """

        if not self.__haveData():
            return None, None

        opts = self.displayCtx.getOpts(self.overlay)
        vidx = opts.getVertex()
        vd   = opts.getVertexData()

        ydata = vd[vidx, :]
        xdata = np.arange(len(ydata))

        return xdata, ydata
