#!/usr/bin/env python
#
# colourbar.py - The ColourBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBar` class, which generates a bitmap
rendering of a colour bar.
"""


import numpy as np

import fsl.utils.notifier                    as notifier
import fsleyes_props                         as props
import fsleyes_widgets.utils.colourbarbitmap as cbarbmp

import fsleyes.displaycontext                as fsldc
import fsleyes.displaycontext.colourmapopts  as cmapopts


def colourBarMinorAxisSize(fontSize):
    """Calculates a good size for the minor axis of a colour bar.

    The minor axis is the axis perpendicular to the colour bar axis.

    :arg fontSize: Font size of colour bar labels, in points.
    """

    # Figure out the font size in pixels
    # (font points are 1/72th of an inch,
    # and we're using inside knowledge
    # that the colourbarbitmap module
    # uses 96 dpi, and a padding of 6
    # pixels).
    fontSize = fontSize
    fontSize = 6 + 96 * fontSize / 72.

    # Fix the minor axis of the colour bar,
    # according to the font size, and a
    # constant size for the colour bar
    return round(2 * fontSize + 40)


class ColourBar(props.HasProperties, notifier.Notifier):
    """A ``ColourBar`` is an object which listens to the properties of a
    :class:`.ColourMapOpts` instance, and automatically generates a colour
    bar bitmap representing the current colour map properties.

    Whenever the colour bar is refreshed, a notification is emitted via the
    :class:`.Notifier` interface.
    """


    orientation = props.Choice(('horizontal', 'vertical'))
    """Whether the colour bar should be vertical or horizontal. """


    labelSide = props.Choice(('top-left', 'bottom-right'))
    """Whether the colour bar labels should be on the top/left, or bottom/right
    of the colour bar (depending upon whether the colour bar orientation is
    horizontal/vertical).
    """


    textColour = props.Colour(default=(1, 1, 1, 1))
    """Colour to use for the colour bar label. """


    bgColour = props.Colour(default=(0, 0, 0, 1))
    """Colour to use for the background. """


    showLabel = props.Boolean(default=True)
    """Toggle the colour bar label (the :attr:`.Display.name` property). """


    showTicks = props.Boolean(default=True)
    """Toggle the tick labels (the :attr:`.ColourMapOpts.displayRange`). """


    fontSize = props.Int(minval=4, maxval=96, default=12)
    """Size of the font used for the text on the colour bar."""


    def __init__(self, overlayList, displayCtx):
        """Create a ``ColourBar``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """


        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)

        self.addGlobalListener(self.name, self.__clearColourBar)

        self.__opts      = None
        self.__display   = None
        self.__size      = (None, None, None)
        self.__colourBar = None

        self.__selectedOverlayChanged()


    @property
    def name(self):
        """Return the name of this ColourBar, used internally for registering
        property listeners.
        """
        return self.__name


    def destroy(self):
        """Must be called when this ``ColourBar`` is no longer needed.

        Removes all registered listeners from the :class:`.OverlayList`,
        :class:`.DisplayContext`, and foom individual overlays.
        """


        self.__overlayList.removeListener('overlays',        self.name)
        self.__displayCtx .removeListener('selectedOverlay', self.name)
        self.__deregisterOverlay()


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes.

        If the newly selected overlay is being displayed with a
        :class:`.ColourMapOpts` instance, various property listeners are
        registered, and the colour bar is refreshed.
        """

        self.__deregisterOverlay()
        self.__registerOverlay()
        self.__clearColourBar()


    def __deregisterOverlay(self):
        """Called when the selected overlay changes. De-registers property
        listeners from any previously-registered :class:`.ColourMapOpts`
        instance.
        """

        if self.__opts is None:
            return

        try:
            opts    = self.__opts
            display = self.__display

            opts   .removeListener('displayRange',    self.name)
            opts   .removeListener('cmap',            self.name)
            opts   .removeListener('negativeCmap',    self.name)
            opts   .removeListener('useNegativeCmap', self.name)
            opts   .removeListener('invert',          self.name)
            opts   .removeListener('gamma',           self.name)
            opts   .removeListener('cmapResolution',  self.name)
            display.removeListener('name',            self.name)

        except fsldc.InvalidOverlayError:
            pass

        self.__opts    = None
        self.__display = None


    def __registerOverlay(self):
        """Called when the selected overlay changes. Registers property
        listeners with the :class:`.ColourMapOpts` instance associated with
        the newly selected overlay.
        """

        overlay = self.__displayCtx.getSelectedOverlay()

        if overlay is None:
            return False

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.opts

        if not isinstance(opts, cmapopts.ColourMapOpts):
            return False

        self.__opts    = opts
        self.__display = display

        opts   .addListener('displayRange',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('cmap',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('negativeCmap',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('useNegativeCmap',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('invert',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('cmapResolution',
                            self.name,
                            self.__clearColourBar)
        opts   .addListener('gamma',
                            self.name,
                            self.__clearColourBar)
        display.addListener('name',
                            self.name,
                            self.__clearColourBar)

        return True


    def __clearColourBar(self, *a):
        """Clears any previously generated colour bar bitmap. """
        self.__colourBar = None
        self.notify()


    def colourBar(self, w, h, scale=1):
        """Returns a bitmap containing the rendered colour bar, rendering it if
        necessary.

        :arg w:     Width in pixels
        :arg h:     Height in pixels
        :arg scale: DPI scaling factor, if applicable.
        """

        if self.__opts is None:
            return None

        if w < 20: w = 20
        if h < 20: h = 20

        if (w, h, scale) == self.__size and self.__colourBar is not None:
            return self.__colourBar

        display        = self.__display
        opts           = self.__opts
        cmap           = opts.cmap
        negCmap        = opts.negativeCmap
        useNegCmap     = opts.useNegativeCmap
        cmapResolution = opts.cmapResolution
        gamma          = opts.realGamma(opts.gamma)
        invert         = opts.invert
        dmin, dmax     = opts.displayRange.x
        label          = display.name

        if self.orientation == 'horizontal':
            if  self.labelSide == 'top-left': labelSide = 'top'
            else:                             labelSide = 'bottom'
        else:
            if  self.labelSide == 'top-left': labelSide = 'left'
            else:                             labelSide = 'right'

        if useNegCmap and dmin == 0.0:
            ticks      = [0.0, 0.5, 1.0]
            ticklabels = ['{:0.3G}'.format(-dmax),
                          '{:0.3G}'.format( dmin),
                          '{:0.3G}'.format( dmax)]
            tickalign  = ['left', 'center', 'right']
        elif useNegCmap:
            ticks      = [0.0, 0.49, 0.51, 1.0]
            ticklabels = ['{:0.3G}'.format(-dmax),
                          '{:0.3G}'.format(-dmin),
                          '{:0.3G}'.format( dmin),
                          '{:0.3G}'.format( dmax)]
            tickalign  = ['left', 'right', 'left', 'right']
        else:
            negCmap    = None
            ticks      = [0.0, 1.0]
            tickalign  = ['left', 'right']
            ticklabels = ['{:0.3G}'.format(dmin),
                          '{:0.3G}'.format(dmax)]

        ticks = np.array(ticks)
        ticks[np.isclose(ticks , 0)] = 0

        if not self.showLabel:
            label = None
        if not self.showTicks:
            ticks      = None
            ticklabels = None

        bitmap = cbarbmp.colourBarBitmap(
            cmap=cmap,
            negCmap=negCmap,
            invert=invert,
            gamma=gamma,
            ticks=ticks,
            ticklabels=ticklabels,
            tickalign=tickalign,
            width=w,
            height=h,
            label=label,
            scale=scale,
            orientation=self.orientation,
            labelside=labelSide,
            textColour=self.textColour,
            fontsize=self.fontSize,
            bgColour=self.bgColour,
            cmapResolution=cmapResolution)

        self.__size      = (w, h, scale)
        self.__colourBar = bitmap

        return bitmap
