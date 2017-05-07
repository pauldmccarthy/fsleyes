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

   TimeSeries
   VoxelTimeSeries
   FEATTimeSeries
   FEATPartialFitTimeSeries
   FEATEVTimeSeries
   FEATResidualTimeSeries
   FEATModelFitTimeSeries
   MelodicTimeSeries
"""


import numpy as np


import fsl.utils.cache    as cache
import fsl.utils.async    as async
import fsleyes_props      as props
import fsleyes.strings    as strings
import fsleyes.colourmaps as fslcm
from . import                dataseries


class TimeSeries(dataseries.DataSeries):
    """Encapsulates time series data from an overlay.  The ``TimeSeries`` class
    is the base-class for all other classes in this module - its
    :meth:`getData` method implements some pre-processing routines which are
    required by the :class:`.TimeSeriesPanel`.

    The following methods are intended to be overridden and/or called by
    sub-class implementations:

    .. autosummary::
       :nosignatures:

       makeLabel
       getData
    """


    def __init__(self, tsPanel, overlay, displayCtx):
        """Create a ``TimeSeries`` instance.

        :arg tsPanel:    The :class:`TimeSeriesPanel` which owns this
                         ``TimeSeries``.

        :arg overlay:    The :class:`.Image` instance to extract the data from.

        :arg displayCtx: The :class:`.DisplayContext`.
        """
        dataseries.DataSeries.__init__(self, overlay)

        self.tsPanel     = tsPanel
        self.displayCtx  = displayCtx


    def makeLabel(self):
        """Return a label for this ``TimeSeries``. """
        display = self.displayCtx.getDisplay(self.overlay)
        return display.name


    def getData(self, xdata=None, ydata=None):
        """Overrides :meth:`.DataSeries.getData`. Returns the data associated
        with this ``TimeSeries`` instance.

        The ``xdata`` and ``ydata`` arguments may be used by sub-classes to
        override the x/y data in the event that they have already performed
        some processing on the data. The default implementation returns
        whatever has been set through :meth:`.DataSeries.setData`.
        """

        dsXData, dsYData = dataseries.DataSeries.getData(self)

        if xdata is None:                    xdata = dsXData
        if ydata is None:                    ydata = dsYData
        if xdata is None or len(xdata) == 0: xdata = np.arange(len(ydata))

        xdata = np.array(xdata, dtype=np.float32)
        ydata = np.array(ydata, dtype=np.float32)

        return xdata, ydata


class VoxelTimeSeries(TimeSeries):
    """A :class:`TimeSeries` sub-class which encapsulates data from a
    specific voxel of a :class:`.Image` overlay.

    The voxel data may be accessed through the :meth:`getData` method, where
    the voxel is defined by current value of the
    :attr:`.DisplayContext.location` property (transformed into the image
    voxel coordinate system).
    """

    def __init__(self, tsPanel, overlay, displayCtx):
        """Create a ``VoxelTimeSeries`` instance.

        :arg tsPanel:    The :class:`TimeSeriesPanel` which owns this
                         ``VoxelTimeSeries``.

        :arg overlay:    The :class:`.Image` instance to extract the data from.

        :arg displayCtx: The :class:`.DisplayContext`.
        """
        TimeSeries.__init__(self, tsPanel, overlay, displayCtx)

        # We use a cache to store data for the
        # most recently accessed voxels. This is
        # done to improve performance on big
        # images (which may be compressed and
        # on disk).
        #
        # TODO You need to invalidate the cache
        #      when the image data changes.
        self.__cache = cache.Cache(maxsize=1000)


    def makeLabel(self):
        """Returns a string representation of this ``VoxelTimeSeries``
        instance.
        """

        display = self.displayCtx.getDisplay(self.overlay)
        opts    = display.getDisplayOpts()
        coords  = opts.getVoxel()

        if coords is not None:
            return '{} [{} {} {}]'.format(display.name,
                                          coords[0],
                                          coords[1],
                                          coords[2])
        else:
            return '{} [out of bounds]'.format(display.name)


    # The PlotPanel uses a new thread to access
    # data every time the displaycontext location
    # changes. So we mark this method as mutually
    # exclusive to prevent multiple
    # near-simultaneous accesses to the same voxel
    # location. The first time that a voxel location
    # is accessed, its data is cached. So when
    # subsequent (blocked) accesses execute, they
    # will hit the cache instead of hitting the disk
    # (which is a good thing).
    @async.mutex
    def getData(self, xdata=None, ydata=None):
        """Returns the data at the current voxel location. The ``xdata`` and
        ``ydata`` parameters may be used by sub-classes to override this
        default behaviour.
        """

        if ydata is None:
            opts = self.displayCtx.getOpts(self.overlay)
            xyz  = opts.getVoxel(vround=True)

            if xyz is None:
                return [], []

            x, y, z = xyz

            ydata = self.__cache.get((x, y, z), None)

            if ydata is None:
                ydata = self.overlay[x, y, z, :]
                self.__cache.put((x, y, z), ydata)

        if xdata is None:
            xdata = np.arange(len(ydata))

        return TimeSeries.getData(self, xdata=xdata, ydata=ydata)


class FEATTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` class for use with :class:`FEATImage`
    instances, containing some extra FEAT specific options.


    The ``FEATTimeSeries`` class acts as a container for several
    ``TimeSeries`` instances, each of which represent some part of a FEAT
    analysis. Therefore, the data returned by a call to
    :meth:`.TimeSeries.getData` on a ``FEATTimeSeries`` instance should not
    be plotted.


    Instead, the :meth:`getModelTimeSeries` method should be used to retrieve
    a list of all the ``TimeSeries`` instances which are associated with the
    ``FEATTimeSeries`` instance - all of these ``TimeSeries`` instances should
    be plotted instead.


    For example, if the :attr:`plotData` and :attr:`plotFullModelFit` settings
    are ``True``, the :meth:`getModelTimeSeries` method will return a list
    containing two ``TimeSeries`` instances - one which will return the FEAT
    analysis input data, and another which will return the full model fit, for
    the voxel in question.


    .. note:: The ``getData`` method of a ``FEATTimeSeries`` instance will
              return the FEAT input data. Therefore, when :attr:`plotData` is
              ``True``, the ``FEATTimeSeries`` instance will itself be included
              in the list returned by :meth:`getModelTimeSeries`.


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
        self.name = '{}_{}'.format(type(self).__name__, id(self))

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


    def getModelTimeSeries(self):
        """Returns a list containing all of the ``TimeSeries`` instances
        which should be plotted in place of this ``FEATTimeSeries``.
        """

        modelts = []

        if self.plotData:              modelts.append(self)
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

        ts = tsType(self.tsPanel,
                    self.overlay,
                    self.displayCtx,
                    self,
                    *args,
                    **kwargs)

        ts.alpha     = self.alpha
        ts.label     = self.label
        ts.lineWidth = self.lineWidth
        ts.lineStyle = self.lineStyle
        ts.label     = ts.makeLabel()

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
                 tsPanel,
                 overlay,
                 displayCtx,
                 parentTs,
                 contrast,
                 fitType,
                 idx):
        """Create a ``FEATPartialFitTimeSeries``.

        :arg tsPanel:    The :class:`TimeSeriesPanel` that owns this
                         ``FEATPartialFitTimeSeries`` instance.

        :arg overlay:    A :class:`.FEATImage` overlay.

        :arg displayCtx: The :class:`.DisplayContext`.

        :arg parentTs:   The :class:`.FEATTimeSeries` instance that has
                         created this ``FEATPartialFitTimeSeries``.

        :arg contrast:   The contrast vector to calculate the partial model
                         fit for.

        :arg fitType:    The model fit type, either ``'full'``, ``'pe'`` or
                         ``'cope'``.

        :arg idx:        If the model fit type is ``'pe'`` or ``'cope'``,
                         the EV/contrast index.
        """
        VoxelTimeSeries.__init__(self, tsPanel, overlay, displayCtx)

        self.parentTs = parentTs
        self.contrast = contrast
        self.fitType  = fitType
        self.idx      = idx


    def getData(self):
        """Returns the partial model fit for the voxel and model fit type
        specified in the constructop.

        See the :meth:`.FEATImage.partialFit` method.
        """
        opts   = self.displayCtx.getOpts(self.overlay)
        coords = opts.getVoxel()

        if coords is None:
            return [], []

        data = self.overlay.partialFit(self.contrast, coords)
        return VoxelTimeSeries.getData(self, ydata=data)


class FEATEVTimeSeries(TimeSeries):
    """A :class:`TimeSeries` class which represents the time course of an
    EV from a FEAT analysis. Instances of this class are created by the
    :class:`FEATTimeSeries` class.
    """

    def __init__(self, tsPanel, overlay, displayCtx, parentTs, idx):
        """Create a ``FEATEVTimeSeries``.

        :arg tsPanel:    The :class:`TimeSeriesPanel` that owns this
                         ``FEATEVTimeSeries`` instance.

        :arg overlay:    A :class:`.FEATImage` overlay.

        :arg displayCtx: The :class:`.DisplayContext`.

        :arg parentTs:   The :class:`.FEATTimeSeries` instance that has
                         created this ``FEATEVTimeSeries``.

        :arg idx:        The EV index.
        """
        TimeSeries.__init__(self, tsPanel, overlay, displayCtx)

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
        data   = design[:, self.idx]

        return TimeSeries.getData(self, ydata=data)


class FEATResidualTimeSeries(VoxelTimeSeries):
    """A :class:`VoxelTimeSeries` class which represents the time course of
    the residuals from a FEAT analysis at a specific voxel. Instances of this
    class are created by the :class:`FEATTimeSeries` class.
    """

    def __init__(self, tsPanel, overlay, displayCtx, parentTs):
        """Create a ``FEATResidualTimeSeries``.

        :arg tsPanel:    The :class:`TimeSeriesPanel` that owns this
                         ``FEATResidualTimeSeries`` instance.

        :arg overlay:    A :class:`.FEATImage` overlay.

        :arg displayCtx: The :class:`.DisplayContext`.

        :arg parentTs:   The :class:`.FEATTimeSeries` instance that has
                         created this ``FEATResidualTimeSeries``.
        """
        VoxelTimeSeries.__init__(self, tsPanel, overlay, displayCtx)
        self.parentTs = parentTs


    def makeLabel(self):
        """Returns a string representation of this ``FEATResidualTimeSeries``
        instance.
        """
        return '{} ({})'.format(self.parentTs.makeLabel(),
                                strings.labels[self])


    def getData(self):
        """Returns the residuals for the current voxel. """

        opts  = self.displayCtx.getOpts(self.overlay)
        voxel = opts.getVoxel()

        if voxel is None:
            return [], []

        x, y, z = voxel
        data    = self.overlay.getResiduals()[x, y, z, :]

        return VoxelTimeSeries.getData(self, ydata=data)


class FEATModelFitTimeSeries(VoxelTimeSeries):
    """A :class:`TimeSeries` class which represents the time course for
    a model fit from a FEAT analysis at a specific voxel. Instances of this
    class are created by the :class:`FEATTimeSeries` class.
    """

    def __init__(self,
                 tsPanel,
                 overlay,
                 displayCtx,
                 parentTs,
                 contrast,
                 fitType,
                 idx):
        """Create a ``FEATModelFitTimeSeries``.

        :arg tsPanel:    The :class:`TimeSeriesPanel` that owns this
                         ``FEATModelFitTimeSeries`` instance.

        :arg overlay:    A :class:`.FEATImage` overlay.

        :arg displayCtx: The :class:`.DisplayContext`.

        :arg parentTs:   The :class:`.FEATTimeSeries` instance that has
                         created this ``FEATModelFitTimeSeries``.

        :arg contrast:   The contrast vector to calculate the partial model
                         fit for.

        :arg fitType:    The model fit type, either ``'full'``, ``'pe'`` or
                         ``'cope'``.

        :arg idx:        If the model fit type is ``'pe'`` or ``'cope'``,
                         the EV/contrast index.
        """

        if fitType not in ('full', 'cope', 'pe'):
            raise ValueError('Unknown model fit type {}'.format(fitType))

        VoxelTimeSeries.__init__(self, tsPanel, overlay, displayCtx)
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

    def getData(self):
        """Returns the FEAT model fit at the current voxel. """

        opts     = self.displayCtx.getOpts(self.overlay)
        voxel    = opts.getVoxel()
        contrast = self.contrast

        if voxel is None:
            return [], []

        data = self.overlay.fit(contrast, voxel)

        return VoxelTimeSeries.getData(self, ydata=data)


class MelodicTimeSeries(TimeSeries):
    """A :class:`.TimeSeries` class which encapsulates the time course for
    one component of a :class:`.MelodicImage`. The :meth:`getData` method
    returns the time course of the component specified by the current
    :class:`.NiftiOpts.volume`.
    """

    def __init__(self, tsPanel, overlay, displayCtx):
        """Create a ``MelodicTimeSeries``.

        :arg tsPanel:    The :class:`.TimeSeriesPanel`.

        :arg overlay:    A :class:`.MelodicImage` overlay.

        :arg displayCtx: The :class:`.DisplayContext`.
        """
        TimeSeries.__init__(self, tsPanel, overlay, displayCtx)


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
        return TimeSeries.getData(self, ydata=ydata)
