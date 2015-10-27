#!/usr/bin/env python
#
# dataseries.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props


class DataSeries(props.HasProperties):
    """A ``DataSeries`` instance encapsulates some data to be plotted by
    a :class:`PlotPanel`, with the data extracted from an overlay in the
    :class:`.OverlayList`. 

    Sub-class implementations must accept an overlay object, pass this
    overlay to the ``DataSeries`` constructor, and override the
    :meth:`getData` method. The overlay is accessible as an instance
    attribute, confusingly called ``overlay``.

    Each``DataSeries`` instance is plotted as a line, with the line
    style defined by properties on the ``DataSeries`` instance,
    such as :attr:`colour`, :attr:`lineWidth` etc.
    """

    colour = props.Colour()
    """Line colour. """

    
    alpha = props.Real(minval=0.0, maxval=1.0, default=1.0, clamped=True)
    """Line transparency."""

    
    label = props.String()
    """Line label (used in the plot legend)."""

    
    lineWidth = props.Choice((0.5, 1, 2, 3, 4, 5))
    """Line width. """

    
    lineStyle = props.Choice(('-', '--', '-.', ':'))
    """Line style. """

    
    def __init__(self, overlay):
        """Create a ``DataSeries``.

        :arg overlay: The overlay from which the data to be plotted is
                      derived. 
        """
        
        self.overlay = overlay
        self.setData([], [])


    def __copy__(self):
        """``DataSeries`` copy operator. Sub-classes with constructors
        that require more than just the overlay object will need to
        implement their own copy operator.
        """
        return type(self)(self.overlay)


    def setData(self, xdata, ydata):
        self.__xdata = xdata
        self.__ydata = ydata 


    def getData(self):
        """This method must be implemented by sub-classes. It must return
        the data to be plotted, as a tuple of the form:
        
            ``(xdata, ydata)``

        where ``xdata`` and ``ydata`` are sequences containing the x/y data
        to be plotted.
        """
        return self.__xdata, self.__ydata
