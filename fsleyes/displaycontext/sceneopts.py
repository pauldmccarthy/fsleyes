#!/usr/bin/env python
#
# sceneopts.py - Provides the SceneOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.SceneOpts` class, which contains display
settings used by :class:`.CanvasPanel` instances.
"""


import copy
import logging

from   fsl.utils.platform import platform  as fslplatform
import fsleyes_props                       as props
import fsleyes.colourmaps                  as fslcm

from . import canvasopts


log = logging.getLogger(__name__)


class SceneOpts(props.HasProperties):
    """The ``SceneOpts`` class defines settings which are used by
    :class:`.CanvasPanel` instances.

    Several of the properties of the ``SceneOpts`` class are defined in the
    :class:`.SliceCanvasOpts` class, so see its documentation for more
    details.
    """


    showCursor      = copy.copy(canvasopts.SliceCanvasOpts.showCursor)
    zoom            = copy.copy(canvasopts.SliceCanvasOpts.zoom)
    bgColour        = copy.copy(canvasopts.SliceCanvasOpts.bgColour)
    cursorColour    = copy.copy(canvasopts.SliceCanvasOpts.cursorColour)
    renderMode      = copy.copy(canvasopts.SliceCanvasOpts.renderMode)
    highDpi         = copy.copy(canvasopts.SliceCanvasOpts.highDpi)


    fgColour = props.Colour(default=(1, 1, 1))
    """Colour to use for foreground items (e.g. labels).

    .. note:: This colour is automatically updated whenever the
              :attr:`.bgColour` is changed. But it can be modified
              independently.
    """


    showColourBar = props.Boolean(default=False)
    """If ``True``, and it is possible to do so, a colour bar is shown on
    the scene.
    """


    colourBarLocation  = props.Choice(('top', 'bottom', 'left', 'right'))
    """This property controls the location of the colour bar, if it is being
    shown.
    """


    colourBarLabelSide = props.Choice(('top-left', 'bottom-right'))
    """This property controls the location of the colour bar labels, relative
    to the colour bar, if it is being shown.
    """


    colourBarSize = props.Percentage(default=100)
    """Size of the major axis of the colour bar, as a proportion of the
    available space.
    """


    labelSize = props.Int(minval=4, maxval=96, default=12, clamped=True)
    """Font size used for any labels drawn on the canvas, including
    orthographic labels, and colour bar labels.
    """


    # NOTE: If you change the maximum performance value,
    #       make sure you update all references to
    #       performance because, for example, the
    #       OrthoEditProfile does numerical comparisons
    #       to it.
    performance = props.Choice((1, 2, 3), default=3, allowStr=True)
    """User controllable performance setting.

    This property is linked to the :attr:`renderMode` property. Setting this
    property to a low value will result in faster rendering time, at the cost
    of increased memory usage and poorer rendering quality.

    See the :meth:`__onPerformanceChange` method.
    """


    movieSyncRefresh = props.Boolean(default=True)
    """Whether, when in movie mode, to synchronise the refresh for GL
    canvases. This is not possible in some platforms/environments. See
    :attr:`.CanvasPanel.movieSyncRefresh`.
    """


    def __init__(self, panel):
        """Create a ``SceneOpts`` instance.

        This method simply links the :attr:`performance` property to the
        :attr:`renderMode` property.
        """

        self.__panel = panel
        self.__name  = '{}_{}'.format(type(self).__name__, id(self))

        self.movieSyncRefresh = self.defaultMovieSyncRefresh

        self.addListener('performance', self.__name, self._onPerformanceChange)
        self.addListener('bgColour',    self.__name, self.__onBgColourChange)
        self._onPerformanceChange()


    @property
    def defaultMovieSyncRefresh(self):
        """
        # In movie mode, the canvas refreshes are
        # performed by the __syncMovieRefresh or
        # __unsyncMovieRefresh methods of the
        # CanvasPanel class. Some platforms/GL
        # drivers/environments seem to have a
        # problem with separate renders/buffer
        # swaps, so we have to use a shitty
        # unsynchronised update routine.
        #
        # These heuristics are not perfect - the
        # movieSyncRefresh property can therefore
        # be overridden by the user.

        """
        renderer        = fslplatform.glRenderer.lower()
        unsyncRenderers = ['gallium', 'mesa dri intel(r)']
        unsync          = any([r in renderer for r in unsyncRenderers])

        return not unsync


    @property
    def panel(self):
        """Return a reference to the ``CanvasPanel`` that owns this
        ``SceneOpts`` instance.
        """
        return self.__panel


    def _onPerformanceChange(self, *a):
        """Called when the :attr:`performance` property changes.

        This method must be overridden by sub-classes to change the values of
        the :attr:`renderMode` property according to the new performance
        setting.
        """
        raise NotImplementedError('The _onPerformanceChange method must'
                                  'be implemented by sub-classes')


    def __onBgColourChange(self, *a):
        """Called when the background colour changes. Updates the
        :attr:`fgColour` to a complementary colour.
        """
        self.fgColour = fslcm.complementaryColour(self.bgColour)
