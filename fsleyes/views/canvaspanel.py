#!/usr/bin/env python
#
# canvaspanel.py - Base class for all panels that display overlay data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasPanel` class, which is the base
class for all panels which display overlays using ``OpenGL``.
"""


import logging

import wx

import fsl.utils.idle                              as idle
import fsl.utils.deprecated                        as deprecated
import fsleyes_props                               as props

import fsleyes.actions                             as actions
import fsleyes.displaycontext                      as displayctx
import fsleyes.controls.overlaylistpanel           as overlaylistpanel
import fsleyes.controls.overlayinfopanel           as overlayinfopanel
import fsleyes.controls.atlaspanel                 as atlaspanel
import fsleyes.controls.overlaydisplaytoolbar      as overlaydisplaytoolbar
import fsleyes.controls.overlaydisplaypanel        as overlaydisplaypanel
import fsleyes.controls.canvassettingspanel        as canvassettingspanel
import fsleyes.controls.locationpanel              as locationpanel
import fsleyes.controls.clusterpanel               as clusterpanel
import fsleyes.controls.lookuptablepanel           as lookuptablepanel
import fsleyes.controls.melodicclassificationpanel as melclasspanel
from . import                                         colourbarpanel
from . import                                         viewpanel


log = logging.getLogger(__name__)


class CanvasPanel(viewpanel.ViewPanel):
    """The ``CanvasPanel`` class is a :class:`.ViewPanel` which is the base
    class for all panels which display overlays using ``OpenGL``
    (e.g. the :class:`.OrthoPanel` and the :class:`.LightBoxPanel`). A
    ``CanvasPanel`` instance uses a :class:`.SceneOpts` instance to control
    much of its functionality. The ``SceneOpts`` instance used by a
    ``CanvasPanel`` can be accessed via the :meth:`sceneOpts` property.


    The ``CanvasPanel`` class contains settings and functionality common to
    all sub-classes, including *movie mode* (see :attr:`movieMode`), the
    ability to show a colour bar (a :class:`.ColourBarPanel`; see
    :attr:`.SceneOpts.showColourBar`), and a number of actions.


    **Sub-class implementations**


    Sub-classes of the ``CanvasPanel`` must do the following:

      1. Add their content to the panel that is accessible via the
         :meth:`contentPanel` property (see the note on
         :ref:`adding content <canvaspanel-adding-content>`).

      2. Override the :meth:`getGLCanvases` method.

      3. Call the :meth:`centrePanelLayout` method in their ``__init__``
         method.

      4. Override the :meth:`centrePanelLayout` method if any custom layout is
         necessary.


    **Actions**


    The following actions are available through a ``CanvasPanel`` (see
    the :mod:`.actions` module):

    .. autosummary::
       :nosignatures:

       screenshot
       movieGif
       showCommandLineArgs
       toggleMovieMode
       toggleDisplaySync
       toggleVolumeSync
       toggleOverlayList
       toggleOverlayInfo
       toggleAtlasPanel
       toggleDisplayToolBar
       toggleDisplayPanel
       toggleCanvasSettingsPanel
       toggleLocationPanel
       toggleClusterPanel
       toggleLookupTablePanel
       toggleClassificationPanel


    .. _canvaspanel-adding-content:


    **Adding content**


    To support colour bar and screenshot functionality, the ``CanvasPanel``
    uses a hierarchy of ``wx.Panel`` instances, depicted in the following
    containment hierarchy diagram:

    .. graphviz::

       digraph canvasPanel {

         graph [size=""];

         node [style="filled",
               shape="box",
               fillcolor="#ddffdd",
               fontname="sans"];

         rankdir="BT";

         1 [label="CanvasPanel"];
         2 [label="Centre panel"];
         3 [label="Custom content (for complex layouts)"];
         4 [label="Container panel"];
         5 [label="ColourBarPanel"];
         6 [label="Content panel"];
         7 [label="Content added by sub-classes"];

         2 -> 1;
         3 -> 2;
         4 -> 2;
         5 -> 4;
         6 -> 4;
         7 -> 6;
       }


    As depicted in the diagram, sub-classes need to add their content to the
    *content panel*. This panel is accessible via the :meth:`contentPanel`
    property.


    The *centre panel* is the :meth:`.ViewPanel.centrePanel`. The *container
    panel* is also available, via :meth:`containerPanel`. Everything in
    the container panel will appear in screenshots (see the :meth:`screenshot`
    method).


    The :meth:`centrePanelLayout` method lays out the centre panel, using the
    :meth:`layoutContainerPanel` method to lay out the colour bar and the
    content panel. The ``centrePanelLayout`` method simply adds the canvas
    container directly to the centre panel. Sub-classes which have more
    advanced layout requirements (e.g.  the :class:`.LightBoxPanel` needs a
    scrollbar) may override the :meth:`centrePanelLayout` method to implement
    their own layout.  These sub-class implementations must:

      1. Call the :meth:`layoutContainerPanel` method.

      2. Add the container panel (accessed via :meth:`containerPanel`)
         to the centre panel (accessed via :meth:`centrePanel`).

      3. Add any other custom content to the centre panel.
    """


    syncLocation = props.Boolean(default=True)
    """If ``True`` (the default), the :attr:`.DisplayContext.location` for
    this ``CanvasPanel`` is linked to the master ``DisplayContext`` location.
    """


    syncOverlayOrder = props.Boolean(default=True)
    """If ``True`` (the default), the :attr:`.DisplayContext.overlayOrder`
    for this ``CanvasPanel`` is linked to the master ``DisplayContext``
    overlay order.
    """


    syncOverlayDisplay = props.Boolean(default=True)
    """If ``True`` (the default), the properties of the :class:`.Display`
    and :class:`.DisplayOpts` instances for every overlay, as managed
    by the :attr:`.DisplayContext` for this ``CanvasPanel``, are linked to
    the properties of all ``Display`` and ``DisplayOpts`` instances managed
    by the master ``DisplayContext`` instance.
    """


    syncOverlayVolume = props.Boolean(default=True)
    """If ``True`` (the default), the volume/timepoint properties of the
    :class:`.DisplayOpts` instances for every overlay, as managed by the
    :attr:`.DisplayContext` for this ``CanvasPanel``, are linked to the
    properties of all ``DisplayOpts`` instances managed by the master
    ``DisplayContext`` instance.
    """


    movieMode = props.Boolean(default=False)
    """If ``True``, and the currently selected overlay (see
    :attr:`.DisplayContext.selectedOverlay`) is a :class:`.Image` instance
    with its display managed by a :class:`.VolumeOpts` instance, the displayed
    volume is changed periodically, according to the :attr:`movieRate`
    property.

    The update is performed on the main application thread via
    ``wx.CallLater``.
    """


    movieRate = props.Int(minval=10, maxval=500, default=400, clamped=True)
    """The movie update rate in milliseconds. The value of this property is
    inverted so that a high value corresponds to a fast rate, which makes
    more sense when displayed as an option to the user.
    """


    movieAxis = props.Choice((0, 1, 2, 3), default=3)
    """Axis along which the movie should be played, relative to the
    currently selected :class:`.Image`.
    """


    movieSyncRefresh = props.Boolean(default=True)
    """Whether, when in movie mode, to synchronise the refresh for GL
    canvases. This is not possible in some platforms/environments.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, sceneOpts):
        """Create a ``CanvasPanel``.

        :arg parent:       The :mod:`wx` parent object.

        :arg overlayList:  The :class:`.OverlayList` instance.

        :arg displayCtx:   The :class:`.DisplayContext` instance.

        :arg sceneOpts:    A :class:`.SceneOpts` instance for this
                           ``CanvasPanel`` - must be created by
                           sub-classes.
        """

        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__opts = sceneOpts

        # Use this name for listener registration,
        # in case subclasses use the FSLeyesPanel.name
        self.__name = 'CanvasPanel_{}'.format(self.name)

        # Bind the sync* properties of this
        # CanvasPanel to the corresponding
        # properties on the DisplayContext
        # instance.
        if displayCtx.getParent() is not None:
            self.bindProps('syncLocation',
                           displayCtx,
                           displayCtx.getSyncPropertyName('worldLocation'))
            self.bindProps('syncLocation',
                           displayCtx,
                           displayCtx.getSyncPropertyName('vertexIndex'))
            self.bindProps('syncOverlayOrder',
                           displayCtx,
                           displayCtx.getSyncPropertyName('overlayOrder'))
            self.bindProps('syncOverlayDisplay', displayCtx)
            self.bindProps('syncOverlayVolume',  displayCtx)

        # If the displayCtx instance does not
        # have a parent, this means that it is
        # a top level instance
        else:
            self.disableProperty('syncLocation')
            self.disableProperty('syncOverlayOrder')
            self.disableProperty('syncOverlayDisplay')
            self.disableProperty('syncOverlayVolume')

        import fsleyes.actions.moviegif as moviegif

        self.centrePanel      = wx.Panel(self)
        self.__containerPanel = wx.Panel(self.centrePanel)
        self.__contentPanel   = wx.Panel(self.__containerPanel)
        self.__movieGifAction = moviegif.MovieGifAction(
            overlayList, displayCtx, self)

        self.bindProps('movieSyncRefresh', sceneOpts)

        self.toggleMovieMode  .bindProps('toggled', self, 'movieMode')
        self.toggleDisplaySync.bindProps('toggled', self, 'syncOverlayDisplay')
        self.toggleVolumeSync .bindProps('toggled', self, 'syncOverlayVolume')
        self.movieGif         .bindProps('enabled', self.__movieGifAction)

        # the __movieModeChanged method is called
        # when movieMode changes, but also when
        # the movie axis, overlay list, or selected
        # overlay changes. This is because, if movie
        # mode is on, but no overlay, or an
        # incompatible overlay, is selected, the
        # movie loop stops. So it needs to be
        # re-started if/when a compatible overlay is
        # selected.
        self.__movieRunning = False
        self            .addListener('movieMode',
                                     self.__name,
                                     self.__movieModeChanged)
        self            .addListener('movieAxis',
                                     self.__name,
                                     self.__movieModeChanged)
        self.overlayList.addListener('overlays',
                                     self.__name,
                                     self.__movieModeChanged)
        self.displayCtx .addListener('selectedOverlay',
                                     self.__name,
                                     self.__movieModeChanged)

        # Canvas/colour bar layout is managed
        # in the layoutContainerPanel method
        self.__colourBar = None

        self.__opts.addListener('colourBarLocation',
                                self.__name,
                                self.__colourBarPropsChanged)
        self.__opts.addListener('showColourBar',
                                self.__name,
                                self.__colourBarPropsChanged)
        self.__opts.addListener('bgColour',
                                self.__name,
                                self.__bgfgColourChanged)
        self.__opts.addListener('fgColour',
                                self.__name,
                                self.__bgfgColourChanged)
        self.__opts.addListener('labelSize',
                                self.__name,
                                self.__labelSizeChanged)


        idle.idle(self.__bgfgColourChanged)


    def destroy(self):
        """Makes sure that any remaining control panels are destroyed
        cleanly, and calls :meth:`.ViewPanel.destroy`.
        """

        if self.__colourBar is not None:
            self.__colourBar.destroy()

        self            .removeListener('movieMode',         self.__name)
        self            .removeListener('movieAxis',         self.__name)
        self.overlayList.removeListener('overlays',          self.__name)
        self.displayCtx .removeListener('selectedOverlay',   self.__name)
        self.sceneOpts  .removeListener('colourBarLocation', self.__name)
        self.sceneOpts  .removeListener('showColourBar',     self.__name)
        self.sceneOpts  .removeListener('bgColour',          self.__name)
        self.sceneOpts  .removeListener('fgColour',          self.__name)
        self.sceneOpts  .removeListener('labelSize',         self.__name)
        self.__movieGifAction.destroy()

        self.__opts           = None
        self.__movieGifAction = None

        viewpanel.ViewPanel.destroy(self)


    @actions.action
    def screenshot(self):
        """Takes a screenshot of the currently displayed scene on this
        ``CanvasPanel``.

        See the :class:`.ScreenshotAction`.
        """
        from fsleyes.actions.screenshot import ScreenshotAction
        ScreenshotAction(self.overlayList, self.displayCtx, self)()


    @actions.action
    def movieGif(self):
        """Generates an animated GIF of the currently displayed scene and
        movie mode settings on this ``CanvasPanel``.

        See the :class:`.MovieGifAction`.
        """
        self.__movieGifAction()


    @actions.action
    def showCommandLineArgs(self):
        """Shows the command line arguments which can be used to re-create
        the currently displayed scene. See the :class:`.ShowCommandLineAction`
        class.
        """
        from fsleyes.actions.showcommandline import ShowCommandLineAction
        ShowCommandLineAction(self.overlayList, self.displayCtx, self)()


    @actions.action
    def applyCommandLineArgs(self):
        """Shows the command line arguments which can be used to re-create
        the currently displayed scene. See the :class:`.ApplyCommandLineAction`
        class.
        """
        from fsleyes.actions.applycommandline import ApplyCommandLineAction
        ApplyCommandLineAction(self.overlayList, self.displayCtx, self)()


    @actions.toggleAction
    def toggleMovieMode(self):
        """Toggles the value of :attr:`movieMode`. """
        # The state of this action gets bound to
        # the movieMode attribute in __init__
        pass


    @actions.toggleAction
    def toggleDisplaySync(self):
        """Toggles the value of :attr:`syncOverlayDisplay`. """
        # The state of this action gets bound to
        # the syncOverlayDisplay attribute in __init__
        pass


    @actions.toggleAction
    def toggleVolumeSync(self):
        """Toggles the value of :attr:`syncOverlayVolume`. """
        # The state of this action gets bound to
        # the syncOverlayVolume attribute in __init__
        pass


    @actions.toggleControlAction(overlaylistpanel.OverlayListPanel)
    def toggleOverlayList(self):
        """Toggles an :class:`.OverlayListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(overlaylistpanel.OverlayListPanel, location=wx.BOTTOM)


    @actions.toggleControlAction(overlayinfopanel.OverlayInfoPanel)
    def toggleOverlayInfo(self, floatPane=False):
        """Toggles an :class:`.OverlayInfoPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(overlayinfopanel.OverlayInfoPanel,
                         location=wx.RIGHT,
                         floatPane=floatPane)


    @actions.toggleControlAction(atlaspanel.AtlasPanel)
    def toggleAtlasPanel(self):
        """Toggles an :class:`.AtlasPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(atlaspanel.AtlasPanel, location=wx.BOTTOM)


    @actions.toggleControlAction(overlaydisplaytoolbar.OverlayDisplayToolBar)
    def toggleDisplayToolBar(self):
        """Toggles an :class:`.OverlayDisplayToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(overlaydisplaytoolbar.OverlayDisplayToolBar,
                         viewPanel=self)


    @actions.toggleControlAction(overlaydisplaypanel.OverlayDisplayPanel)
    def toggleDisplayPanel(self, floatPane=False):
        """Toggles an :class:`.OverlayDisplayPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(overlaydisplaypanel.OverlayDisplayPanel,
                         floatPane=floatPane,
                         location=wx.LEFT)


    @actions.toggleControlAction(canvassettingspanel.CanvasSettingsPanel)
    def toggleCanvasSettingsPanel(self, floatPane=False):
        """Toggles a :class:`.CanvasSettingsPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(canvassettingspanel.CanvasSettingsPanel,
                         canvasPanel=self,
                         floatPane=floatPane,
                         location=wx.LEFT)


    @actions.toggleControlAction(locationpanel.LocationPanel)
    def toggleLocationPanel(self):
        """Toggles a :class:`.LocationPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        from fsleyes.views.orthopanel import OrthoPanel

        # location history only shown in ortho panels
        self.togglePanel(locationpanel.LocationPanel,
                         showHistory=isinstance(self, OrthoPanel),
                         location=wx.BOTTOM)


    @actions.toggleControlAction(clusterpanel.ClusterPanel)
    def toggleClusterPanel(self):
        """Toggles a :class:`.ClusterPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(clusterpanel.ClusterPanel, location=wx.TOP)


    @actions.toggleControlAction(lookuptablepanel.LookupTablePanel)
    def toggleLookupTablePanel(self):
        """Toggles a :class:`.LookupTablePanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(lookuptablepanel.LookupTablePanel, location=wx.RIGHT)


    @actions.toggleControlAction(melclasspanel.MelodicClassificationPanel)
    def toggleClassificationPanel(self):
        """Toggles a :class:`.MelodicClassificationPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(melclasspanel.MelodicClassificationPanel,
                         location=wx.RIGHT,
                         canvasPanel=self)


    @property
    def sceneOpts(self):
        """Returns the :class:`.SceneOpts` instance used by this
        ``CanvasPanel``.
        """
        return self.__opts


    @property
    def contentPanel(self):
        """Returns the ``wx.Panel`` to which sub-classes must add their content.
        See the note on :ref:`adding content <canvaspanel-adding-content>`.
        """
        return self.__contentPanel


    @property
    def containerPanel(self):
        """Returns the ``wx.Panel`` which contains the
        :class:`.ColourBarPanel` if it is being displayed, and the content
        panel. See the note on
        :ref:`adding content <canvaspanel-adding-content>`.
        """
        return self.__containerPanel


    @property
    def colourBarCanvas(self):
        """If a colour bar is being displayed, this method returns
        the :class:`.ColourBarCanvas` instance which is used by the
        :class:`.ColourBarPanel` to render the colour bar.

        Otherwise, ``None`` is returned.
        """
        if self.__colourBar is not None:
            return self.__colourBar.getCanvas()
        return None


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use sceneOpts instead')
    def getSceneOptions(self):
        """Returns the :class:`.SceneOpts` instance used by this
        ``CanvasPanel``.
        """
        return self.__opts


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use contentPanel instead')
    def getContentPanel(self):
        """Returns the ``wx.Panel`` to which sub-classes must add their content.
        See the note on :ref:`adding content <canvaspanel-adding-content>`.
        """
        return self.__contentPanel


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use containerPanel instead')
    def getContainerPanel(self):
        """Returns the ``wx.Panel`` which contains the
        :class:`.ColourBarPanel` if it is being displayed, and the content
        panel. See the note on
        :ref:`adding content <canvaspanel-adding-content>`.
        """
        return self.__containerPanel


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use colourBarCanvas instead')
    def getColourBarCanvas(self):
        """If a colour bar is being displayed, this method returns
        the :class:`.ColourBarCanvas` instance which is used by the
        :class:`.ColourBarPanel` to render the colour bar.

        Otherwise, ``None`` is returned.
        """
        if self.__colourBar is not None:
            return self.__colourBar.getCanvas()
        return None


    def getGLCanvases(self):
        """This method must be overridden by subclasses, and must return a
        list containing all :class:`.SliceCanvas` instances which are being
        displayed.
        """
        raise NotImplementedError(
            'getGLCanvases has not been implemented '
            'by {}'.format(type(self).__name__))


    def centrePanelLayout(self):
        """Lays out the centre panel. This method may be overridden by
        sub-classes which need more advanced layout logic. See the note on
        :ref:`adding content <canvaspanel-adding-content>`
        """

        self.layoutContainerPanel()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.__containerPanel, flag=wx.EXPAND, proportion=1)
        self.centrePanel.SetSizer(sizer)

        self.PostSizeEvent()


    def layoutContainerPanel(self):
        """Creates a ``wx.Sizer``, and uses it to lay out the colour bar panel
        and canvas panel. The sizer object is returned.

        This method is used by the default :meth:`centrePanelLayout` method,
        and is available for custom sub-class implementations to use.
        """

        sopts = self.sceneOpts

        if not sopts.showColourBar:

            if self.__colourBar is not None:
                sopts.unbindProps('colourBarLabelSide',
                                  self.__colourBar.colourBar,
                                  'labelSide')
                sopts.unbindProps('colourBarSize',
                                  self.__colourBar.canvas,
                                  'barSize')
                sopts.unbindProps('highDpi', self.__colourBar.canvas)

                self.__colourBar.destroy()
                self.__colourBar.Destroy()
                self.__colourBar = None

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
            self.__containerPanel.SetSizer(sizer)
            return

        if self.__colourBar is None:
            self.__colourBar = colourbarpanel.ColourBarPanel(
                self.__containerPanel,
                self.overlayList,
                self.displayCtx,
                self.frame)

            bg = sopts.bgColour
            fg = sopts.fgColour
            fs = sopts.labelSize
            self.__colourBar.colourBar.textColour = fg
            self.__colourBar.colourBar.bgColour   = bg
            self.__colourBar.colourBar.fontSize   = fs

            sopts.bindProps('colourBarLabelSide',
                            self.__colourBar.colourBar,
                            'labelSide')
            sopts.bindProps('colourBarSize',
                            self.__colourBar.canvas,
                            'barSize')
            sopts.bindProps('highDpi', self.__colourBar.canvas)

        if   sopts.colourBarLocation in ('top', 'bottom'):
            self.__colourBar.colourBar.orientation = 'horizontal'
        elif sopts.colourBarLocation in ('left', 'right'):
            self.__colourBar.colourBar.orientation = 'vertical'

        if sopts.colourBarLocation in ('top', 'bottom'):
            sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            sizer = wx.BoxSizer(wx.HORIZONTAL)

        if sopts.colourBarLocation in ('top', 'left'):
            sizer.Add(self.__colourBar,    flag=wx.EXPAND)
            sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
        else:
            sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
            sizer.Add(self.__colourBar,    flag=wx.EXPAND)

        self.__containerPanel.SetSizer(sizer)


    def __colourBarPropsChanged(self, *a):
        """Called when any colour bar display properties are changed (see
        :class:`.SceneOpts`). Calls :meth:`canvasPanelLayout`.
        """
        self.centrePanelLayout()


    def __labelSizeChanged(self, *a, **kwa):
        """Called when the :class:`.SceneOpts.lablSize` changes.  If a colour
        bar is being displayed, it is updated, and the panel layout is
        refreshed.
        """
        sopts = self.sceneOpts
        if self.__colourBar is not None:
            self.__colourBar.canvas.colourBar.fontSize = sopts.labelSize
        wx.CallAfter(self.Layout)


    def __bgfgColourChanged(self, *a, **kwa):
        """Called when the :class:`.SceneOpts.bgColour` or
        :class:`.SceneOpts.fgColour` properties change.  Updates
        background/foreground colours.

        The :attr:`.SliceCanvasOpts.bgColour` properties are bound to
        ``SceneOpts.bgColour``,(see :meth:`.HasProperties.bindProps`), so we
        don't need to manually update them.

        :arg refresh: Must be passed as a keyword argument. If ``True`` (the
                      default), this ``OrthoPanel`` is refreshed.
        """
        refresh = kwa.pop('refresh', True)

        sceneOpts = self.sceneOpts
        cpanel    = self.contentPanel
        canvases  = self.getGLCanvases()
        bg        = sceneOpts.bgColour
        fg        = sceneOpts.fgColour

        cpanel.SetBackgroundColour([c * 255 for c in bg])
        cpanel.SetForegroundColour([c * 255 for c in fg])

        if self.__colourBar is not None:
            canvas = self.__colourBar.canvas
            cbar   = self.__colourBar.colourBar
            cbar.textColour = fg
            cbar.bgColour   = bg
            canvases.append(canvas)

        if refresh:
            self.Refresh()
            self.Update()


    def __movieModeChanged(self, *a):
        """Called when the :attr:`movieMode` property changes. If it has been
        enabled, calls :meth:`__movieUpdate`, to start the movie loop.
        """

        # The fsl.utils.idle idle loop timeout
        # defaults to 200 milliseconds, which can
        # cause delays in frame updates. So when
        # movie mode is on, we bump up the rate.
        def startMovie():
            idle.setIdleTimeout(10)
            if not self.__movieLoop(startLoop=True):
                idle.setIdleTimeout(None)

        # The __movieModeChanged method is called
        # on the props event queue. Here we make
        # sure that __movieLoop() is called *off*
        # the props event queue, by calling it from
        # the idle loop.
        if self.movieMode: idle.idle(startMovie)
        else:              idle.setIdleTimeout(None)


    def __movieLoop(self, startLoop=False):
        """Manages the triggering of the next movie frame. This method is
        called by :meth:`__movieModeChanged` when :attr:`movieMode` changes
        and when the selected overlay changes, and also by
        :meth:`__syncMovieRefresh` and :meth:`__unsyncMovieRefresh` while
        the movie loop is running, to trigger the next frame.

        :arg startLoop: This is set to ``True`` when called from
                        :meth:`__movieModeChanged`. If ``True``, and the movie
                        loop is already running, this method does nothing.

        """

        # Movie loop is already running, nothing to do.
        if startLoop and self.__movieRunning:
            return True

        # Attempt to show the next frame -
        # __movieFrame returns True if the
        # movie is continuing, False if it
        # has ended.
        self.__movieRunning = self.__movieFrame()

        return self.__movieRunning


    def canRunMovie(self, overlay, opts):
        """Returns ``True`` or ``False``, depending on whether movie mode
        is possible with the given z`overlay`` and ``opts``.
        """

        import fsl.data.image as fslimage
        import fsl.data.mesh  as fslmesh

        axis = self.movieAxis

        # 3D movies are good for all overlays
        if axis < 3:
            return True

        # 4D Nifti images are all good
        if isinstance(overlay, fslimage.Nifti) and \
           len(overlay.shape) > 3              and \
           overlay.shape[3] > 1                and \
           isinstance(opts, displayctx.VolumeOpts):
            return True

        # Mesh surfaces with N-D
        # vertex data are all good
        if isinstance(overlay, fslmesh.Mesh) and \
           opts.vertexDataLen() > 1:
            return True

        return False


    def getMovieFrame(self, overlay, opts):
        """Returns the current movie frame for the given overlay.

        A movie frame is typically a sequentially increasing number in
        some minimum/maximum range, e.g. a voxel or volume index.

        This method may be overridden by sub-classes for custom behaviour
        (e.g. the :class:`.Scene3DPanel`).
        """

        axis = self.movieAxis

        def nifti():
            if axis < 3: return opts.getVoxel(vround=False)[axis]
            else:        return opts.volume

        def mesh():
            if axis < 3: return other()
            else:        return opts.vertexDataIndex

        def other():
            return self.displayCtx.location.getPos(axis)

        import fsl.data.image as fslimage
        import fsl.data.mesh  as fslmesh

        if   isinstance(overlay, fslimage.Nifti): return nifti()
        elif isinstance(overlay, fslmesh.Mesh):   return mesh()
        else:                                     return other()


    def doMovieUpdate(self, overlay, opts):
        """Called by :meth:`__movieFrame`. Updates the properties on the
        given ``opts`` instance to move forward one frame in the movie.

        This method may be overridden by sub-classes for custom behaviour
        (e.g. the :class:`.Scene3DPanel`).

        :returns:   A value which identifies the current movie frame. This may
                    be a volume or voxel index, or a world coordinate location
                    on one axis.
        """

        axis = self.movieAxis

        def nifti():

            limit = overlay.shape[axis]

            # This method has been called off the props
            # event queue (see __movieModeChanged).
            # Therefore, all listeners on the opts.volume
            # or DisplayContext.location  properties
            # should be called immediately, in these
            # assignments.
            #
            # When the movie axis == 3 (time), this means
            # that image texture refreshes should be
            # triggered and, after the opts.volume
            # assignment, all affected GLObjects should
            # return ready() == False.
            if axis == 3:
                if opts.volume >= limit - 1: opts.volume  = 0
                else:                        opts.volume += 1

                frame = opts.volume

            else:
                voxel = opts.getVoxel()
                if voxel[axis] >= limit - 1: voxel[axis]  = 0
                else:                        voxel[axis] += 1

                self.displayCtx.location = opts.transformCoords(
                    voxel, 'voxel', 'display')

                frame = voxel[axis]
            return frame

        def mesh():

            if axis == 3:
                limit = opts.vertexDataLen()
                val   = opts.vertexDataIndex

                if val >= limit - 1: val  = 0
                else:                val += 1

                opts.vertexDataIndex = val

                return val

            else:
                return other()

        def other():

            bmin, bmax = opts.bounds.getRange(axis)
            delta      = (bmax - bmin) / 75.0

            pos = self.displayCtx.location.getPos(axis)

            if pos >= bmax: pos = bmin
            else:           pos = pos + delta

            self.displayCtx.location.setPos(axis, pos)
            return pos

        import fsl.data.image as fslimage
        import fsl.data.mesh  as fslmesh

        if   isinstance(overlay, fslimage.Nifti): frame = nifti()
        elif isinstance(overlay, fslmesh.Mesh):   frame = mesh()
        else:                                     frame = other()

        return frame


    def __movieFrame(self):
        """Called by :meth:`__movieLoop`.

        If the currently selected overlay (see
        :attr:`.DisplayContext.selectedOverlay`) is a 4D :class:`.Image` being
        displayed as a ``volume`` (see the :class:`.VolumeOpts` class), the
        :attr:`.NiftiOpts.volume` property is incremented and all
        GL canvases in this ``CanvasPanel`` are refreshed.

        :returns: ``True`` if the movie loop was started, ``False`` otherwise.
        """

        from . import scene3dpanel

        if self.destroyed():   return False
        if not self.movieMode: return False

        overlay  = self.displayCtx.getSelectedOverlay()
        canvases = self.getGLCanvases()

        if overlay is None:
            return False

        opts = self.displayCtx.getOpts(overlay)

        if not self.canRunMovie(overlay, opts):
            return False

        # We want the canvas refreshes to be
        # synchronised. So we 'freeze' them
        # while changing the image volume, and
        # then refresh them all afterwards.
        for c in canvases:
            c.FreezeDraw()
            c.FreezeSwapBuffers()

        self.doMovieUpdate(overlay, opts)

        # Now we get refs to *all* GLObjects managed
        # by every canvas - we have to wait until
        # they are all ready to be drawn before we
        # can refresh the canvases.  Note that this
        # is only necessary when the movie axis == 3
        globjs = [c.getGLObject(o)
                  for c in canvases
                  for o in self.overlayList]
        globjs = [g for g in globjs if g is not None]

        def allReady():
            return all([g.ready() for g in globjs])

        # Figure out the movie rate - the
        # number of seconds to wait until
        # triggering the next frame.
        rate    = self.movieRate
        rateMin = self.getAttribute('movieRate', 'minval')
        rateMax = self.getAttribute('movieRate', 'maxval')

        # Special case/hack - if this is a Scene3DPanel,
        # and the movie axis is X/Y/Z, we always
        # use a fast rate. Instead, the Scene3dPanel
        # will increase/decrease the rotation angle
        # to speed up/slow down the movie instead.
        if isinstance(self, scene3dpanel.Scene3DPanel) and self.movieAxis < 3:
            rate = rateMax

        rate = (rateMin + (rateMax - rate)) / 1000.0

        # Use sync or unsync refresh regime
        if self.movieSyncRefresh: update = self.__syncMovieRefresh
        else:                     update = self.__unsyncMovieRefresh

        # Refresh the canvases when all
        # GLObjects are ready to be drawn.
        idle.idleWhen(update, allReady, canvases, rate, pollTime=rate / 10)

        return True


    def __unsyncMovieRefresh(self, canvases, rate):
        """Called by :meth:`__movieUpdate`. Updates all canvases in an
        unsynchronised manner.

        Ideally all canvases should be drawn off-screen (i.e. rendered to the
        back buffer), and then all refreshed together (back and front buffers
        swapped). Unfortunately some OpenGL drivers seem to have trouble with
        this approach, and require drawing and front/back buffer swaps to be
        done at the same time. This method is used for those drivers.

        :arg canvases: List of canvases to update. It is assumed that
                       ``FreezeDraw`` and ``FreezeSwapBuffers`` has been
                       called on every canvas.
        :arg rate:     Delay to trigger the next movie update.
        """

        for c in canvases:
            c.ThawDraw()
            c.ThawSwapBuffers()
            c.Refresh()

        idle.idle(self.__movieLoop, after=rate)


    def __syncMovieRefresh(self, canvases, rate):
        """Updates all canvases in a synchronised manner. All canvases are
        refreshed, and then the front/back buffers are swapped on each of
        them.

        :arg canvases: List of canvases to update. It is assumed that
                       ``FreezeDraw`` and ``FreezeSwapBuffers`` has been
                       called on every canvas.
        :arg rate:     Delay to trigger the next movie update.
        """

        for c in canvases:
            c.ThawDraw()
            c.Refresh()

        for c in canvases:
            c.ThawSwapBuffers()
            c.SwapBuffers()

        idle.idle(self.__movieLoop, after=rate)
