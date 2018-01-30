#!/usr/bin/env python
#
# dataseries.py - The DataSeries class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`DataSeries` class, the base class for
classes used by :class:`.PlotPanel` views for plotting data.
"""

import logging

import fsleyes_props as props


log = logging.getLogger(__name__)


class DataSeries(props.HasProperties):
    """A ``DataSeries`` instance encapsulates some data to be plotted by
    a :class:`PlotPanel`, with the data extracted from an overlay in the
    :class:`.OverlayList`.

    Sub-class implementations must:

      - Accept an overlay object, :class:`.OverlayList`,
        :class:`.DisplayContext`, and :class:`.PlotPanel` in their
        ``__init__`` method, and pass these through to
        :meth:`.DataSeries.__init__`.
      - Override the :meth:`getData` method
      - Override the :meth:`redrawProperties` method if necessary


    The overlay is accessible as an instance attribute, confusingly called
    ``overlay``.


    .. note:: Some ``DataSeries`` instances may not be associated with
              an overlay (e.g. series imported loaded a text file). In
              this case, the ``overlay`` attribute will be ``None``.


    Each``DataSeries`` instance is plotted as a line, with the line
    style defined by properties on the ``DataSeries`` instance,
    such as :attr:`colour`, :attr:`lineWidth` etc.
    """


    colour = props.Colour()
    """Line colour. """


    enabled = props.Boolean(default=True)
    """Draw or not draw?"""


    alpha = props.Real(minval=0.0, maxval=1.0, default=1.0, clamped=True)
    """Line transparency."""


    label = props.String()
    """Line label (used in the plot legend)."""


    lineWidth = props.Choice((0.5, 1, 2, 3, 4, 5))
    """Line width. """


    lineStyle = props.Choice(('-', '--', '-.', ':'))
    """Line style. """


    def __init__(self, overlay, overlayList, displayCtx, plotPanel):
        """Create a ``DataSeries``.

        :arg overlay:     The overlay from which the data to be plotted is
                          retrieved.  May be ``None``.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotPanel:   The :class:`.PlotPanel` that owns this
                          ``DataSeries``.
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__overlay     = overlay
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__plotPanel   = plotPanel
        self.setData([], [])

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message. """
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    def __hash__(self):
        """Returns a hash for this ``DataSeries`` instance."""
        return hash(id(self))


    @property
    def name(self):
        """Returns a unique name for this ``DataSeries`` instance. """
        return self.__name


    @property
    def overlay(self):
        """Returns the overlay associated with this ``DataSeries`` instance.
        """
        return self.__overlay


    @property
    def overlayList(self):
        """Returns the :class:`.OverlayList`.
        """
        return self.__overlayList


    @property
    def displayCtx(self):
        """Returns the :class:`.DisplayContext`.
        """
        return self.__displayCtx


    @property
    def plotPanel(self):
        """Returns the :class:`.PlotPanel` that owns this ``DataSeries``
        instance.
        """
        return self.__plotPanel


    def destroy(self):
        """This method must be called when this ``DataSeries`` instance is no
        longer needed. This implementation may be overridden by sub-classes
        which need to perform any clean-up operations. Sub-class
        implementations should call this implementation.
        """
        self.__overlay     = None
        self.__overlayList = None
        self.__displayCtx  = None
        self.__plotPanel   = None


    def redrawProperties(self):
        """Returns a list of all properties which, when their values change,
        should result in this ``DataSeries`` being re-plotted. This method
        may be overridden by sub-classes.
        """

        return self.getAllProperties()[0]


    def setData(self, xdata, ydata):
        """Set the data to be plotted. This method is irrelevant if a
        ``DataSeries`` sub-class has overridden :meth:`getData`.
        """
        self.__xdata = xdata
        self.__ydata = ydata


    def getData(self):
        """This method should be overridden by sub-classes. It must return
        the data to be plotted, as a tuple of the form:

            ``(xdata, ydata)``

        where ``xdata`` and ``ydata`` are sequences containing the x/y data
        to be plotted.

        The default implementation returns the data that has been set via the
        :meth:`setData` method.
        """
        return self.__xdata, self.__ydata
