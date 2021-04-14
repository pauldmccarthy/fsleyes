#!/usr/bin/env python
#
# locationpanel.py - provides the LocationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LocationPanel` class, a *FSLeyes control*
panel which shows information about the current display location.
"""


import logging
import itertools as it

import wx
import wx.html as wxhtml

import numpy as np

import fsl.transform.affine           as affine
import fsl.utils.settings             as fslsettings
import fsl.data.image                 as fslimage
import fsl.data.mesh                  as fslmesh
import fsl.data.constants             as constants

import fsleyes_props                  as props
import fsleyes_widgets.floatspin      as floatspin
import fsleyes_widgets.notebook       as notebook
import fsleyes_widgets.elistbox       as elistbox
import fsleyes_widgets.utils.status   as status
import fsleyes_widgets.utils.typedict as td

import fsleyes.controls.controlpanel  as ctrlpanel
import fsleyes.views.canvaspanel      as canvaspanel
import fsleyes.panel                  as fslpanel
import fsleyes.strings                as strings


log = logging.getLogger(__name__)


class LocationPanel(ctrlpanel.ControlPanel):
    """The ``LocationPanel`` is a panel which contains controls allowing the
    user to view and modify the :attr:`.DisplayContext.location` property.

    A ``LocationPanel`` is intended to be contained within a
    :class:`.CanvasPanel`, and looks something like this:

    .. image:: images/locationpanel.png
       :scale: 50%
       :align: center

    By default, the ``LocationPanel`` contains a notebook with two pages:

      - The :class:`LocationInfoPanel` contains information about the currently
        displayed location, and controls allowing the user to change the
        location.

      - The :class:`LocationHistoryPanel` contains a list of previously visited
        locations, and allows the user to revisit those locations.

    The history panel is optional - if the ``showHistory`` parameter to
    ``__init__`` is ``False`` then only the information panel will be shown.
    """


    @staticmethod
    def supportedViews():
        """The ``LocationPanel`` is restricted for use with
        :class:`.CanvasPanel` views.
        """
        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.BOTTOM}


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 viewPanel,
                 showHistory=False):
        """Creat a ``LocationPanel``.

        :arg parent:      The :mod:`wx` parent object, assumed to be a
                          :class:`.CanvasPanel`.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg viewPanel:   The :class:`.ViewPanel` instance.

        :arg showHistory: Defaults to ``False``. If ``True``, create and
                          display a :class:`LocationHistoryPanel`.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, viewPanel)

        # only use a notebook if showing history panel
        if showHistory:
            self.__notebook = notebook.Notebook(self,
                                                style=wx.LEFT | wx.VERTICAL,
                                                border=0)
            subparent       = self.__notebook
        else:
            subparent       = self
            self.__notebook = None

        # We always create an info panel
        self.__info = LocationInfoPanel(
            subparent, overlayList, displayCtx, viewPanel.frame)

        # We don't always create a history panel
        if showHistory:
            self.__history = LocationHistoryPanel(
                subparent, overlayList, displayCtx, viewPanel.frame, parent)
            self.__notebook.AddPage(self.__info,
                                    strings.labels[self, 'info'])
            self.__notebook.AddPage(self.__history,
                                    strings.labels[self, 'history'])
        else:
            self.__history = None

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        if showHistory:
            self.__sizer.Add(self.__notebook, flag=wx.EXPAND, proportion=1)
        else:
            self.__sizer.Add(self.__info, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)
        self.Layout()


    def destroy(self):
        """Must be called when this ``LocationPanel`` is no longer needed. """

        if self.__history is not None:
            self.__history.destroy()

        self.__info.destroy()
        self.__info    = None
        self.__history = None

        ctrlpanel.ControlPanel.destroy(self)


class LocationInfoPanel(fslpanel.FSLeyesPanel):
    """The ``LocationInfoPanel`` is a panel which is embedded in the
    :class:`LocationPanel`, and which contains controls allowing the user to
    view and modify the :attr:`.DisplayContext.location` property.


    The ``LocationInfoPanel`` contains two main sections:

      - A collection of controls which show the current
        :attr:`.DisplayContext.location`

      - A ``wx.html.HtmlWindow`` which displays information about the current
        :attr:`.DisplayContext.location` for all overlays in the
        :class:`.OverlayList`.


    **NIFTI overlays**


    The ``LocationInfoPanel`` is primarily designed to work with
    :class:`.Image` overlays. If the :attr:`.DisplayContext.selectedOverlay`
    is an :class:`.Image`, or has an associated reference image (see
    :meth:`.DisplayOpts.referenceImage`), the ``LocationInfoPanel`` will
    display the current :class:`.DisplayContext.location` in both the the
    voxel coordinates and world coordinates of the ``Image`` instance.


    **Other overlays**


    If the :attr:`.DisplayContext.selectedOverlay` is not an :class:`.Image`,
    or does not have an associated reference image, the ``LocationInfoPanel``
    will display the current :attr:`.DisplayContext.location` as-is (i.e. in
    the display coordinate system); furthermore, the voxel location controls
    will be disabled.


    **Location updates**


    The :data:`DISPLAYOPTS_BOUNDS` and :data:`DISPLAYOPTS_INFO` dictionaries
    contain lists of property names that the :class:`.LocationInfoPanel`
    listens on for changes, so it knows when the location widgets, and
    information about the currenty location, need to be refreshed. For
    example, when the :attr`.NiftiOpts.volume` property of a :class:`.Nifti`
    overlay changes, the volume index, and potentially the overlay
    information, needs to be updated.
    """


    voxelLocation = props.Point(ndims=3, real=False)
    """If the currently selected overlay is a :class:`.Image` instance , this
    property tracks the current :attr:`.DisplayContext.location` in voxel
    coordinates.
    """


    worldLocation = props.Point(ndims=3, real=True)
    """For :class:`.Image` overlays, this property tracks the current
    :attr:`.DisplayContext.location` in the image world coordinates. For other
    overlay types, this property tracks the current location in display
    coordinates.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):

        fslpanel.FSLeyesPanel.__init__(self,
                                       parent,
                                       overlayList,
                                       displayCtx,
                                       frame,
                                       kbFocus=True)

        # Whenever the selected overlay changes,
        # a reference to it and its DisplayOpts
        # instance is stored, as property listeners
        # are registered on it (and need to be
        # de-registered later on).
        self.__registeredOverlay = None
        self.__registeredDisplay = None
        self.__registeredOpts    = None

        self.__column1 = wx.Panel(self)
        self.__column2 = wx.Panel(self)
        self.__info    = wxhtml.HtmlWindow(self)

        # HTMLWindow does not use
        # the parent font by default,
        # so we force it to at least
        # have the parent font size
        self.__info.SetStandardFonts(self.GetFont().GetPointSize())

        self.__worldLabel = wx.StaticText(
            self.__column1, label=strings.labels[self, 'worldLocation'])
        self.__volumeLabel = wx.StaticText(
            self.__column1, label=strings.labels[self, 'volume'])
        self.__voxelLabel = wx.StaticText(
            self.__column2, label=strings.labels[self, 'voxelLocation'])

        worldX, worldY, worldZ = props.makeListWidgets(
            self.__column1,
            self,
            'worldLocation',
            slider=False,
            spin=True,
            showLimits=False,
            mousewheel=True)

        voxelX, voxelY, voxelZ = props.makeListWidgets(
            self.__column2,
            self,
            'voxelLocation',
            slider=False,
            spin=True,
            spinWidth=7,
            showLimits=False,
            mousewheel=True)

        self.__worldX = worldX
        self.__worldY = worldY
        self.__worldZ = worldZ
        self.__voxelX = voxelX
        self.__voxelY = voxelY
        self.__voxelZ = voxelZ
        self.__volume = floatspin.FloatSpinCtrl(
            self.__column2,
            width=7,
            style=floatspin.FSC_MOUSEWHEEL | floatspin.FSC_INTEGER)

        self.__column1Sizer = wx.BoxSizer(wx.VERTICAL)
        self.__column2Sizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer        = wx.BoxSizer(wx.HORIZONTAL)

        self.__column1Sizer.Add(self.__worldLabel,  flag=wx.EXPAND)
        self.__column1Sizer.Add(self.__worldX,      flag=wx.EXPAND)
        self.__column1Sizer.Add(self.__worldY,      flag=wx.EXPAND)
        self.__column1Sizer.Add(self.__worldZ,      flag=wx.EXPAND)
        self.__column1Sizer.Add(self.__volumeLabel, flag=wx.ALIGN_RIGHT)

        self.__column2Sizer.Add(self.__voxelLabel, flag=wx.EXPAND)
        self.__column2Sizer.Add(self.__voxelX,     flag=wx.EXPAND)
        self.__column2Sizer.Add(self.__voxelY,     flag=wx.EXPAND)
        self.__column2Sizer.Add(self.__voxelZ,     flag=wx.EXPAND)
        self.__column2Sizer.Add(self.__volume,     flag=wx.EXPAND)

        self.__sizer.Add(self.__column1, flag=wx.EXPAND)
        self.__sizer.Add((5, -1))
        self.__sizer.Add(self.__column2, flag=wx.EXPAND)
        self.__sizer.Add((5, -1))
        self.__sizer.Add(self.__info,    flag=wx.EXPAND, proportion=1)

        self.__column1.SetSizer(self.__column1Sizer)
        self.__column2.SetSizer(self.__column2Sizer)
        self          .SetSizer(self.__sizer)

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__selectedOverlayChanged)
        self.displayCtx .addListener('selectedOverlay',
                                     self.name,
                                     self.__selectedOverlayChanged)
        self.displayCtx .addListener('overlayOrder',
                                     self.name,
                                     self.__overlayOrderChanged)
        self.displayCtx .addListener('location',
                                     self.name,
                                     self.__displayLocationChanged)
        self.addListener(            'voxelLocation',
                                     self.name,
                                     self.__voxelLocationChanged)
        self.addListener(            'worldLocation',
                                     self.name,
                                     self.__worldLocationChanged)

        self.__selectedOverlayChanged()

        self.__worldLabel .SetMinSize(self.__calcWorldLabelMinSize())
        self.__voxelLabel .SetMinSize(self.__voxelLabel .GetBestSize())
        self.__volumeLabel.SetMinSize(self.__volumeLabel.GetBestSize())
        self.__column1    .SetMinSize(self.__column1    .GetBestSize())
        self.__column2    .SetMinSize(self.__column2    .GetBestSize())
        self.__info       .SetMinSize((100, 100))

        # Keyboard navigation - see FSLeyesPanel
        self.setNavOrder((self.__worldX,
                          self.__worldY,
                          self.__worldZ,
                          self.__voxelX,
                          self.__voxelY,
                          self.__voxelZ,
                          self.__volume))

        self.Layout()

        self.__minSize = self.__sizer.GetMinSize()
        self.SetMinSize(self.__minSize)


    def destroy(self):
        """Must be called when this ``LocationInfoPanel`` is no longer needed.
        Removes property listeners and calls :meth:`.FSLeyesPanel.destroy`.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.displayCtx .removeListener('location',        self.name)

        self.__deregisterOverlay()

        fslpanel.FSLeyesPanel.destroy(self)


    def GetMinSize(self):
        """Returns the minimum size for this ``LocationInfoPanel``.

        Under Linux/GTK, the ``wx.agw.lib.aui`` layout manager seems to
        arbitrarily adjust the minimum sizes of some panels. Therefore, The
        minimum size of the ``LocationInfoPanel`` is calculated in
        :meth:`__init__`, and is fixed.
        """
        return self.__minSize


    def DoGetBestClientSize(self):
        """Returns the best size for this ``LocationInfoPanel``.
        """
        return self.__minSize


    def __calcWorldLabelMinSize(self):
        """Calculates the minimum size that the world label (the label which
        shows the coordinate space of the currently selected overlay) needs.
        Called by the :meth:`__init__` method.

        The world label displays different things depending on the currently
        selected overlay. But we want it to be a fixed size. So this method
        calculates the size of all possible values that the world label will
        display, and returns the maximum size. This is then used as the
        minimum size for the world label.
        """

        dc = wx.ClientDC(self.__worldLabel)

        width, height = 0, 0

        labelPref = strings.labels[self, 'worldLocation']
        labelSufs = [
            strings.anatomy['Nifti',
                            'space',
                            constants.NIFTI_XFORM_UNKNOWN],
            strings.anatomy['Nifti',
                            'space',
                            constants.NIFTI_XFORM_SCANNER_ANAT],
            strings.anatomy['Nifti',
                            'space',
                            constants.NIFTI_XFORM_ALIGNED_ANAT],
            strings.anatomy['Nifti',
                            'space',
                            constants.NIFTI_XFORM_TALAIRACH],
            strings.anatomy['Nifti',
                            'space',
                            constants.NIFTI_XFORM_MNI_152],
            strings.labels[self, 'worldLocation', 'unknown']
        ]

        for labelSuf in labelSufs:

            w, h = dc.GetTextExtent(labelPref + labelSuf)

            if w > width:  width  = w
            if h > height: height = h

        return width + 5, height


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` is changed. Registered with the new overlay,
        and refreshes the ``LocationInfoPanel`` interface accordingly.
        """

        self.__deregisterOverlay()

        if len(self.overlayList) == 0:
            self.__updateWidgets()
            self.__updateLocationInfo()

        else:
            self.__registerOverlay()
            self.__updateWidgets()
            self.__displayLocationChanged()


    def __registerOverlay(self):
        """Registers property listeners with the :class:`.Display` and
        :class:`.DisplayOpts` instances associated with the currently
        selected overlay.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        display = self.displayCtx.getDisplay(overlay)
        opts    = display.opts

        self.__registeredOverlay = overlay
        self.__registeredDisplay = display
        self.__registeredOpts    = opts

        # The properties that we need to
        # listen for are specified in the
        # DISPLAYOPTS_BOUNDS and
        # DISPLAYOPTS_INFO dictionaries.
        boundPropNames = DISPLAYOPTS_BOUNDS.get(opts, [], allhits=True)
        infoPropNames  = DISPLAYOPTS_INFO  .get(opts, [], allhits=True)
        boundPropNames = it.chain(*boundPropNames)
        infoPropNames  = it.chain(*infoPropNames)

        # DisplayOpts instances get re-created
        # when an overlay type is changed, so
        # we need to re-register when this happens.
        display.addListener('overlayType',
                            self.name,
                            self.__selectedOverlayChanged)

        for n in boundPropNames:
            opts.addListener(n, self.name, self.__boundsOptsChanged)
        for n in infoPropNames:
            opts.addListener(n, self.name, self.__infoOptsChanged)

        # Enable the volume widget if the
        # overlay is a NIFTI image with more
        # than three dimensions, and bind
        # the widget to the volume property
        # of  the associated NiftiOpts instance
        if isinstance(overlay, fslimage.Nifti) and overlay.ndim > 3:

            props.bindWidget(self.__volume,
                             opts,
                             'volume',
                             floatspin.EVT_FLOATSPIN)

            opts.addListener('volumeDim', self.name, self.__volumeDimChanged)

            self.__volume     .Enable()
            self.__volumeLabel.Enable()
            self.__volumeDimChanged()

        # Or, if the overlay is a mesh which
        # has some time series data associated
        # with it
        elif isinstance(overlay, fslmesh.Mesh):

            props.bindWidget(self.__volume,
                             opts,
                             'vertexDataIndex',
                             floatspin.EVT_FLOATSPIN)

            opts.addListener('vertexData', self.name, self.__vertexDataChanged)
            self.__vertexDataChanged()

        else:
            self.__volume.SetRange(0, 0)
            self.__volume.SetValue(0)
            self.__volume.Disable()


    def __deregisterOverlay(self):
        """De-registers property listeners with the :class:`.Display` and
        :class:`.DisplayOpts` instances associated with the previously
        registered overlay.
        """

        opts    = self.__registeredOpts
        display = self.__registeredDisplay
        overlay = self.__registeredOverlay

        if overlay is None:
            return

        self.__registeredOpts    = None
        self.__registeredDisplay = None
        self.__registeredOverlay = None

        boundPropNames = DISPLAYOPTS_BOUNDS.get(opts, [], allhits=True)
        infoPropNames  = DISPLAYOPTS_INFO  .get(opts, [], allhits=True)
        boundPropNames = it.chain(*boundPropNames)
        infoPropNames  = it.chain(*infoPropNames)

        if display is not None:
            display.removeListener('overlayType', self.name)

        for p in boundPropNames: opts.removeListener(p, self.name)
        for p in infoPropNames:  opts.removeListener(p, self.name)

        if isinstance(overlay, fslimage.Nifti) and overlay.ndim > 3:
            props.unbindWidget(self.__volume,
                               opts,
                               'volume',
                               floatspin.EVT_FLOATSPIN)
            opts.removeListener('volumeDim', self.name)

        elif isinstance(overlay, fslmesh.Mesh):
            props.unbindWidget(self.__volume,
                               opts,
                               'vertexDataIndex',
                               floatspin.EVT_FLOATSPIN)
            opts.removeListener('vertexData', self.name)


    def __volumeDimChanged(self, *a):
        """Called when the selected overlay is a :class:`.Nifti`, and its
        :attr:`.NiftiOpts.volumeDim` property changes. Updates the volume
        widget.
        """
        overlay = self.__registeredOverlay
        opts    = self.__registeredOpts
        volume  = opts.volume
        vdim    = opts.volumeDim + 3

        self.__volume.SetRange(0, overlay.shape[vdim] - 1)
        self.__volume.SetValue(volume)
        self.__infoOptsChanged()


    def __vertexDataChanged(self, *a):
        """Called when the selected overlay is a :class:`.Mesh`, and
        its :attr:`.MeshOpts.vertexData` property changes. Updates the volume
        widget.
        """

        opts    = self.__registeredOpts
        vd      = opts.getVertexData()
        vdi     = opts.vertexDataIndex
        enabled = vd is not None and vd.shape[1] > 1

        self.__volume     .Enable(enabled)
        self.__volumeLabel.Enable(enabled)

        if enabled:
            self.__volume.SetRange(0, vd.shape[1] - 1)
            self.__volume.SetValue(vdi)

        self.__infoOptsChanged()


    def __boundsOptsChanged(self, *a):
        """Called when a :class:`.DisplayOpts` property associated
        with the currently selected overlay, and listed in the
        :data:`DISPLAYOPTS_BOUNDS` dictionary, changes. Refreshes the
        ``LocationInfoPanel`` interface accordingly.
        """
        self.__updateWidgets()
        self.__displayLocationChanged()


    def __infoOptsChanged(self, *a):
        """Called when a :class:`.DisplayOpts` property associated
        with the currently selected overlay, and listed in the
        :data:`DISPLAYOPTS_INFO` dictionary, changes. Refreshes the
        ``LocationInfoPanel`` interface accordingly.
        """
        self.__displayLocationChanged()


    def __overlayOrderChanged(self, *a):
        """Called when the :attr:`.DisplayContext.overlayOrder` changes,
        Refreshes the information panel.
        """
        self.__displayLocationChanged()


    def __updateWidgets(self):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__displayOptsChanged` methods.  Enables/disables the
        voxel/world location and volume controls depending on the currently
        selected overlay (or reference image).
        """

        overlay = self.__registeredOverlay
        opts    = self.__registeredOpts

        if overlay is not None: refImage = opts.referenceImage
        else:                   refImage = None

        haveRef = refImage is not None

        self.__voxelX     .Enable(haveRef)
        self.__voxelY     .Enable(haveRef)
        self.__voxelZ     .Enable(haveRef)
        self.__voxelLabel .Enable(haveRef)

        ######################
        # World location label
        ######################

        label = strings.labels[self, 'worldLocation']

        if haveRef: label += strings.anatomy[refImage,
                                             'space',
                                             refImage.getXFormCode()]
        else:       label += strings.labels[ self,
                                             'worldLocation',
                                             'unknown']

        self.__worldLabel.SetLabel(label)

        ####################################
        # Voxel/world location widget limits
        ####################################

        # Figure out the limits for the
        # voxel/world location widgets
        if haveRef:
            opts     = self.displayCtx.getOpts(refImage)
            v2w      = opts.getTransform('voxel', 'world')
            shape    = refImage.shape[:3]
            vlo      = [0, 0, 0]
            vhi      = np.array(shape) - 1
            wlo, whi = affine.axisBounds(shape, v2w)
            wstep    = refImage.pixdim[:3]
        else:
            vlo     = [0, 0, 0]
            vhi     = [0, 0, 0]
            wbounds = self.displayCtx.bounds[:]
            wlo     = wbounds[0::2]
            whi     = wbounds[1::2]
            wstep   = [1, 1, 1]

        log.debug('Setting voxelLocation limits: {} - {}'.format(vlo, vhi))
        log.debug('Setting worldLocation limits: {} - {}'.format(wlo, whi))

        # Update the voxel and world location limits,
        # but don't trigger a listener callback, as
        # this would change the display location.
        widgets = [self.__worldX, self.__worldY, self.__worldZ]
        with props.suppress(self, 'worldLocation'), \
             props.suppress(self, 'voxelLocation'):

            for i in range(3):
                self.voxelLocation.setLimits(i, vlo[i], vhi[i])
                self.worldLocation.setLimits(i, wlo[i], whi[i])
                widgets[i].SetIncrement(wstep[i])


    def __displayLocationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` changes.
        Propagates the change on to the :attr:`voxelLocation`
        and :attr:`worldLocation` properties.

        .. note:: Because the :attr:`.DisplayContext.location`,
                  :attr:`voxelLocation` and :attr:`worldLocation` properties
                  are all linked through property listeners (see
                  :meth:`props.HasProperties.addListener`), we need to be a
                  bit careful to avoid circular updates. Therefore, each of
                  the :meth:`__displayLocationChanged`,
                  :meth:`__worldLocationChanged` and
                  :meth:`__voxelLocationChanged` methods use the
                  :meth:`__prePropagate`, :meth:`__propagate`, and
                  :meth:`__postPropagate` methods to propagate changes
                  between the three location properties.
        """

        if not self or self.destroyed:
            return

        if len(self.overlayList) == 0:       return
        if self.__registeredOverlay is None: return

        self.__prePropagate()
        self.__propagate('display', 'voxel')
        self.__propagate('display', 'world')
        self.__postPropagate()
        self.__updateLocationInfo()


    def __worldLocationChanged(self, *a):
        """Called when the :attr:`worldLocation` changes.  Propagates the
        change on to the :attr:`voxelLocation` and
        :attr:`.DisplayContext.location` properties.
        """

        if len(self.overlayList) == 0:       return
        if self.__registeredOverlay is None: return

        self.__prePropagate()
        self.__propagate('world', 'voxel')
        self.__propagate('world', 'display')
        self.__postPropagate()
        self.__updateLocationInfo()


    def __voxelLocationChanged(self, *a):
        """Called when the :attr:`voxelLocation` changes.  Propagates the
        change on to the :attr:`worldLocation` and
        :attr:`.DisplayContext.location` properties.
        """

        if len(self.overlayList) == 0:       return
        if self.__registeredOverlay is None: return

        self.__prePropagate()
        self.__propagate('voxel', 'world')
        self.__propagate('voxel', 'display')
        self.__postPropagate()
        self.__updateLocationInfo()


    def __prePropagate(self):
        """Called by the :meth:`__displayLocationChanged`,
        :meth:`__worldLocationChanged` and :meth:`__voxelLocationChanged`
        methods.

        Disables notification of all location property listeners, so
        circular updates do not occur.
        """

        self           .disableNotification('voxelLocation')
        self           .disableNotification('worldLocation')
        self.displayCtx.disableListener(    'location', self.name)

        self.Freeze()


    def __propagate(self, source, target):
        """Called by the :meth:`__displayLocationChanged`,
        :meth:`__worldLocationChanged` and :meth:`__voxelLocationChanged`
        methods. Copies the coordinates from the ``source`` location to the
        ``target`` location. Valid values for the ``source`` and ``target``
        are:

        =========== ==============================================
        ``display`` The :attr:`.DisplayContext.location` property.
        ``voxel``   The :attr:`voxelLocation` property.
        ``world``   The :attr:`worldLocation` property.
        =========== ==============================================
        """

        if   source == 'display': coords = self.displayCtx.location.xyz
        elif source == 'voxel':   coords = self.voxelLocation.xyz
        elif source == 'world':   coords = self.worldLocation.xyz

        refImage = self.__registeredOpts.referenceImage

        if refImage is not None:
            opts    = self.displayCtx.getOpts(refImage)
            xformed = opts.transformCoords([coords],
                                           source,
                                           target,
                                           vround=target == 'voxel')[0]
        else:
            xformed = coords

        log.debug('Updating location ({} {} -> {} {})'.format(
            source, coords, target, xformed))

        if   target == 'display': self.displayCtx.location.xyz = xformed
        elif target == 'voxel':   self.voxelLocation      .xyz = xformed
        elif target == 'world':   self.worldLocation      .xyz = xformed


    def __postPropagate(self):
        """Called by the :meth:`__displayLocationChanged`,
        :meth:`__worldLocationChanged` and :meth:`__voxelLocationChanged`
        methods.

        Re-enables the property listeners that were disabled by the
        :meth:`__postPropagate` method.
        """
        self           .enableNotification('voxelLocation')
        self           .enableNotification('worldLocation')
        self.displayCtx.enableListener(    'location', self.name)

        self.Thaw()
        self.Refresh()
        self.Update()


    def __updateLocationInfo(self):
        """Called whenever the :attr:`.DisplayContext.location` changes.
        Updates the HTML panel which displays information about all overlays
        in the :class:`.OverlayList`.
        """

        if len(self.overlayList) == 0 or self.__registeredOverlay is None:
            self.__info.SetPage('')
            return

        # Reverse the overlay order so they
        # are ordered the same on the info
        # page as in the overlay list panel
        displayCtx = self.displayCtx
        overlays   = reversed(displayCtx.getOrderedOverlays())
        selOvl     = displayCtx.getSelectedOverlay()
        lines      = []

        dswarn = self.__genDisplaySpaceWarning()
        if dswarn is not None:
            fmt = '<span style="color: #ff0000"><b>{}</b></span>'
            lines.append(fmt.format(dswarn))

        for overlay in overlays:

            display = displayCtx.getDisplay(overlay)
            opts    = display.opts

            if not display.enabled:
                continue

            info = None
            title = '<b>{}</b>'.format(display.name)

            # For mesh overlays, if the current location
            # corresponds to a vertex, show some info
            # about that vertex
            if isinstance(overlay, fslmesh.Mesh):
                info = self.__genMeshInfo(overlay, opts)
            elif isinstance(overlay, fslimage.Image):
                info = self.__genImageInfo(overlay, opts)
            else:
                info = '{}'.format(strings.labels[self, 'noData'])

            # Indent info for unselected overlays,
            # to make the info for the selected
            # overlay a bit more obvious.
            colourFmt = '<span style="color: #6060ff">{}</span>'
            if overlay is selOvl:
                title = colourFmt.format(title)
                if info is not None:
                    info = colourFmt.format(info)

            lines.append(title)

            if info is not None:
                lines.append(info)

        self.__info.SetPage('<br>'.join(lines))
        self.__info.Refresh()


    def __genDisplaySpaceWarning(self):
        """Generate a warning if images with different orientations and/or
        fields-of-view are loaded.
        """
        images  = [o for o in self.overlayList
                   if isinstance(o, fslimage.Image)]

        for i in images[1:]:
            if not i.sameSpace(images[0]):
                return strings.messages[self, 'displaySpaceWarning']

        return None


    def __genMeshInfo(self, ovl, opts):
        """Generate an info line for the given :class:`.Mesh` overlay. """
        vidx  = opts.getVertex()
        vd    = opts.getVertexData()
        vdidx = opts.vertexDataIndex

        if vidx is None:
            info = '[no vertex]'

        else:
            # some vertex data has been
            # loaded for this mesh.
            if vd is not None:

                # time series/multiple data points per
                # vertex - display the time/data index
                # as well
                if vd.shape[1] > 1:
                    info = '[{}, {}]: {}'.format(vidx,
                                                 vdidx,
                                                 vd[vidx, vdidx])

                # Only one scalar value per vertex -
                # don't bother showing the vertex
                # data index
                else:
                    info = '[{}]: {}'.format(vidx, vd[vidx, vdidx])

            else:
                info = '[{}]'.format(vidx)
        return info


    def __genImageInfo(self, ovl, opts):
        """Generate an info line for the given :class:`.Image` overlay. """

        vloc = opts.getVoxel()

        if vloc is not None:
            vloc = tuple(int(v) for v in vloc)
            vloc = opts.index(vloc)
            vval = ovl[vloc]
            vloc = ' '.join(map(str, vloc))

            if not np.isscalar(vval):
                vval = np.asscalar(vval)

            if opts.overlayType == 'label':
                lbl = opts.lut.get(int(vval))
                if lbl is None: lbl = 'no label'
                else:           lbl = lbl.name
                info = '[{}]: {} / {}'.format(vloc, vval, lbl)

            elif opts.overlayType == 'complex':
                if opts.component in ('real', 'imag'):
                    info = '[{}]: {}'.format(vloc, vval)
                else:
                    cval = opts.getComponent(vval)
                    info = '[{}]: {} ({}: {})'.format(
                        vloc, vval, opts.component, cval)
            else:
                info = '[{}]: {}'.format(vloc, vval)

        else:
            info = strings.labels[self, 'outOfBounds']
        return info


DISPLAYOPTS_BOUNDS = td.TypeDict({
    'DisplayOpts' : ['bounds'],
    'MeshOpts'    : ['refImage'],
})
"""Different :class:`.DisplayOpts` types have different properties which
affect the current overlay bounds.  Therefore, when the current overlay
changes (as dictated by the :attr:`.DisplayContext.selectedOverlay`
property),the :meth:`__registerOverlay` method registers property
listeners on the properties specified in this dictionary.
"""


DISPLAYOPTS_INFO = td.TypeDict({
    'NiftiOpts'   : ['volume'],
    'MeshOpts'    : ['vertexDataIndex'],
    'ComplexOpts' : ['component']
})
"""Different :class:`.DisplayOpts` types have different properties which
affect the current overlay location information.  Therefore, when the current
overlay changes the :meth:`__registerOverlay` method registers property
listeners on the properties specified in this dictionary.
"""


class LocationHistoryPanel(fslpanel.FSLeyesPanel):
    """The ``LocationHistoryPanel`` is a panel which is embedded in the
    :class:`LocationPanel`, and which contains a list of locations
    previously visited by the user.
    """

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 frame,
                 canvasPanel,
                 limit=500):
        """Create a ``LocationHistoryPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` instance.

        :arg canvasPanel: The :class:`.CanvasPanel` which owns this
                          ``LocationHistoryPanel``.

        :arg limit:       Maximum number of locations to save before dropping
                          old locations.
        """
        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__profile  = None
        self.__limit    = limit
        self.__canvas   = canvasPanel
        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__load     = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__save     = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__clear    = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__hint     = wx.StaticText(self)
        self.__list     = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_REVERSE   |
                   elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE   |
                   elistbox.ELB_EDITABLE  |
                   elistbox.ELB_SCROLL_BUTTONS))

        self.__load .SetLabel(strings.labels[self, 'load'])
        self.__save .SetLabel(strings.labels[self, 'save'])
        self.__clear.SetLabel(strings.labels[self, 'clear'])
        self.__hint .SetLabel(strings.labels[self, 'hint'])

        self.__btnSizer.Add((10, 1))
        self.__btnSizer.Add(self.__hint, flag=wx.EXPAND, proportion=1)
        self.__btnSizer.Add(self.__load)
        self.__btnSizer.Add((10, 1))
        self.__btnSizer.Add(self.__save)
        self.__btnSizer.Add((10, 1))
        self.__btnSizer.Add(self.__clear)
        self.__btnSizer.Add((10, 1))

        self.__sizer.Add(self.__btnSizer,
                         flag=wx.EXPAND | wx.TOP | wx.BOTTOM,
                         border=3)
        self.__sizer.Add(self.__list,
                         flag=wx.EXPAND,
                         proportion=1)
        self.SetSizer(self.__sizer)
        self.Layout()

        self.__list .Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        self.__load .Bind(wx.EVT_BUTTON,                 self.__onLoad)
        self.__save .Bind(wx.EVT_BUTTON,                 self.__onSave)
        self.__clear.Bind(wx.EVT_BUTTON,                 self.__onClear)

        self.__canvas.events.register(self.name,
                                      self.__profileChanged,
                                      'profile')
        self.__profileChanged()


    def destroy(self):
        """Must be called when this ``LocationHistoryPanel`` is no longer
        needed.
        """
        self.__deregisterProfile()
        self.__canvas.events.deregister(self.name, 'profile')
        self.__canvas = None
        fslpanel.FSLeyesPanel.destroy(self)


    def getHistory(self):
        """Returns a list containing the currently displayed location history.
        Each entry in the list is a tuple containing the coordinates, and any
        comment that the user has addded.
        """

        history = []

        for i in range(self.__list.GetCount()):
            location = self.__list.GetItemData(i)
            comment  = self.__list.GetItemLabel(i)
            history.append((location, comment))

        return history


    def __registerProfile(self, profile):
        """Registers a mouse event listener with the given ``profile``. """
        if profile is not None:
            self.__profile = profile
            self.__profile.registerHandler('LeftMouseUp',
                                           self.name,
                                           self.__onMouseUp)


    def __deregisterProfile(self):
        """De-registers listeners that have previously been registered with a
        :class:`.Profile` object.
        """
        if self.__profile is not None:
            self.__profile.deregisterHandler('LeftMouseUp', self.name)
            self.__profile = None


    def __profileChanged(self, *a):
        """Called when the :attr:`.CanvasPanel.profile` changes. Re-registers
        mouse event listeners with the new :class:`.Profile` object.
        """
        self.__deregisterProfile()
        self.__registerProfile(self.__canvas.currentProfile)


    def __addLocation(self, worldLoc, comment=None):
        """Add a location to the location history.

        :arg worldLoc: Location in world coordinates
        :arg comment:  Comment about the location
        """

        if comment is None:
            comment = ''

        label = '[{:7.2f}, {:7.2f}, {:7.2f}]'.format(*worldLoc)
        label = wx.StaticText(self.__list, label=label)

        self.__list.Append(comment, clientData=worldLoc, extraWidget=label)


    def __onMouseUp(self, ev, canvas, mouseLoc, canvasLoc):
        """Called on mouse up events. Adds the mouse location (in the world
        coordinate system) to the location history list.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        opts    = self.displayCtx.getOpts(overlay)
        overlay = opts.referenceImage

        if overlay is not None:
            opts     = self.displayCtx.getOpts(overlay)
            worldLoc = opts.transformCoords(canvasLoc, 'display', 'world')
        else:
            worldLoc = canvasLoc

        self.__addLocation(worldLoc)

        while self.__list.GetCount() > self.__limit:
            self.__list.Delete(0)


    def __onListSelect(self, ev):
        """Called when a location is selected from the location history list.

        Sets the :attr:`.DisplayContext.worldLocation` accordingly.
        """
        self.displayCtx.worldLocation = ev.data


    def __onLoad(self, ev):
        """Called when the *load* button is pushed. Prompts the user to select
        a file, then loads a history from that file.
        """

        msg     = strings.messages[self, 'load']
        fromDir = fslsettings.read('loadSaveOverlayDir')
        dlg     = wx.FileDialog(self,
                                message=msg,
                                defaultDir=fromDir,
                                wildcard='*.txt',
                                style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        errTitle = strings.titles[  self, 'loadError']
        errMsg   = strings.messages[self, 'loadError'].format(dlg.GetPath())
        with status.reportIfError(errTitle, errMsg, raiseError=False):
            history = loadLocationHistory(dlg.GetPath())

        self.__list.Clear()
        for loc, comment  in history:
            self.__addLocation(loc, comment)


    def __onSave(self, ev):
        """Called when the *save* button is pushed. Prompts the user to select
        a file name, then saves the current history to that file.
        """
        history = self.getHistory()
        msg     = strings.messages[self, 'save']
        defDir  = fslsettings.read('loadSaveOverlayDir')
        dlg     = wx.FileDialog(self,
                                message=msg,
                                defaultDir=defDir,
                                wildcard='*.txt',
                                style=wx.FD_SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            return

        errTitle = strings.titles[  self, 'saveError']
        errMsg   = strings.messages[self, 'saveError'].format(dlg.GetPath())
        with status.reportIfError(errTitle, errMsg, raiseError=False):
            saveLocationHistory(history, dlg.GetPath())


    def __onClear(self, ev):
        """Called when the *clear* button is pushed. Clears the current
        history.
        """
        self.__list.Clear()


def loadLocationHistory(filename):
    """Loads a location history from the given ``filename``. A location history
    file contains one location on each line, where the X, Y, and Z coordinates
    are separated by a space character. All remaining characters on the line
    are treated as the location comment. For example::

        1.27 4.23 1.63 this is a comment
        5.25 2.66 1.23

    Returns a list containing the location history, in the same format as that
    returned by :meth:`.LocationHistoryPanel.getHistory`.
    """

    history = []

    with open(filename, 'rt') as f:

        lines = f.read().strip().split('\n')

        for line in lines:
            line = line.strip()

            if line == '':
                continue

            try:
                parts = line.split(None, 3)
                loc   = [float(parts[0]),
                         float(parts[1]),
                         float(parts[2])]

                if len(parts) > 3: comment = parts[3]
                else:              comment = ''

                history.append((loc, comment))

            except Exception:
                raise ValueError('Invalid location history '
                                 'format: {}'.format(line))

    return history


def saveLocationHistory(history, filename):
    """Saves the given location ``history`` to the given ``filename``. See
    :func:`loadLocationHistory` and :meth:`LocationHistoryPanel.getHistory`.
    """

    lines = []

    for loc, comment in history:
        loc = '{:0.8f} {:0.8f} {:0.8f}'.format(*loc)
        lines.append('{} {}'.format(loc, comment))

    with open(filename, 'wt') as f:
        f.write('\n'.join(lines))
