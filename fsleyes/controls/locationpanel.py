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

import fsl.utils.transform            as transform
import fsl.data.image                 as fslimage
import fsl.data.constants             as constants

import fsleyes_props                  as props
import fsleyes_widgets.floatspin      as floatspin
import fsleyes_widgets.utils.typedict as td

import fsleyes.panel                  as fslpanel
import fsleyes.strings                as strings


log = logging.getLogger(__name__)


class LocationPanel(fslpanel.FSLeyesPanel):
    """The ``LocationPanel`` is a panel which contains controls allowing the
    user to view and modify the :attr:`.DisplayContext.location` property. A
    ``LocationPanel`` is intended to be contained within a
    :class:`.CanvasPanel`, and looks something like this:

    .. image:: images/locationpanel.png
       :scale: 50%
       :align: center


    The ``LocationPanel`` contains two main sections:

      - A collection of controls which show the current
        :attr:`.DisplayContext.location`

      - A ``wx.html.HtmlWindow`` which displays information about the current
        :attr:`.DisplayContext.location` for all overlays in the
        :class:`.OverlayList`.


    **NIFTI overlays**


    The ``LocationPanel`` is primarily designed to work with :class:`.Image`
    overlays. If the :attr:`.DisplayContext.selectedOverlay` is an
    :class:`.Image`, or has an associated reference image (see the
    :meth:`.DisplayOpts.getReferenceImage` method), the ``LocationPanel``
    will display the current :class:`.DisplayContext.location` in both the
    the voxel coordinates and world coordinates of the ``Image`` instance.


    **Other overlays**


    If the :attr:`.DisplayContext.selectedOverlay` is not an :class:`.Image`,
    or does not have an associated reference image, the ``LocationPanel`` will
    display the current :attr:`.DisplayContext.location` as-is (i.e. in the
    display coordinate system); furthermore, the voxel location controls will
    be disabled.


    **Location updates**


    The :data:`DISPLAYOPTS_BOUNDS` and :data:`DISPLAYOPTS_INFO` dictionaries
    contain lists of property names that the :class:`.LocationPanel` listens
    on for changes, so it knows when the location widgets, and information
    about the currenty location, need to be refreshed. For example, when the
    :attr`.NiftiOpts.volume` property of a :class:`.Nifti` overlay changes,
    the volume index, and potentially the overlay information, needs to be
    updated.
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
        """Creat a ``LocationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

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

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._displayCtx .addListener('overlayOrder',
                                      self._name,
                                      self.__overlayOrderChanged)
        self._displayCtx .addListener('location',
                                      self._name,
                                      self.__displayLocationChanged)
        self.addListener(             'voxelLocation',
                                      self._name,
                                      self.__voxelLocationChanged)
        self.addListener(             'worldLocation',
                                      self._name,
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
        """Must be called when this ``LocationPanel`` is no longer needed.
        Removes property listeners and calls :meth:`.FSLeyesPanel.destroy`.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        self.__deregisterOverlay()

        fslpanel.FSLeyesPanel.destroy(self)


    def GetMinSize(self):
        """Returns the minimum size for this ``LocationPanel``.

        Under Linux/GTK, the ``wx.agw.lib.aui`` layout manager seems to
        arbitrarily adjust the minimum sizes of some panels. Therefore, The
        minimum size of the ``LocationPanel`` is calculated in
        :meth:`__init__`, and is fixed.
        """
        return self.__minSize


    def DoGetBestClientSize(self):
        """Returns the best size for this ``LocationPanel``.
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

        return width + 5, height + 5


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` is changed. Registered with the new overlay,
        and refreshes the ``LocationPanel`` interface accordingly.
        """

        self.__deregisterOverlay()

        if len(self._overlayList) == 0:
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

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

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
                            self._name,
                            self.__selectedOverlayChanged)

        for n in boundPropNames:
            opts.addListener(n, self._name, self.__boundsOptsChanged)
        for n in infoPropNames:
            opts.addListener(n, self._name, self.__infoOptsChanged)

        # Enable the volume widget if the
        # overlay is a 4D image, and bind
        # the widget to the volume property
        # of  the associated NiftiOpts
        # instance
        is4D = isinstance(overlay, fslimage.Nifti) and \
               len(overlay.shape) >= 4             and \
               overlay.shape[3] > 1

        if is4D:
            props.bindWidget(
                self.__volume, opts, 'volume', floatspin.EVT_FLOATSPIN)

            self.__volume.SetRange(0, overlay.shape[3] - 1)
            self.__volume.SetValue(opts.volume)

            self.__volume     .Enable()
            self.__volumeLabel.Enable()
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
            display.removeListener('overlayType', self._name)

        for p in boundPropNames: opts.removeListener(p, self._name)
        for p in infoPropNames:  opts.removeListener(p, self._name)

        is4D      = isinstance(overlay, fslimage.Nifti) and \
                    len(overlay.shape) >= 4             and \
                    overlay.shape[3] > 1

        if is4D:
            props.unbindWidget(self.__volume,
                               opts,
                               'volume',
                               floatspin.EVT_FLOATSPIN)


    def __boundsOptsChanged(self, *a):
        """Called when a :class:`.DisplayOpts` property associated
        with the currently selected overlay, and listed in the
        :data:`DISPLAYOPTS_BOUNDS` dictionary, changes. Refreshes the
        ``LocationPanel`` interface accordingly.
        """
        self.__updateWidgets()
        self.__displayLocationChanged()


    def __infoOptsChanged(self, *a):
        """Called when a :class:`.DisplayOpts` property associated
        with the currently selected overlay, and listed in the
        :data:`DISPLAYOPTS_INFO` dictionary, changes. Refreshes the
        ``LocationPanel`` interface accordingly.
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

        if overlay is not None: refImage = opts.getReferenceImage()
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
            opts     = self._displayCtx.getOpts(refImage)
            v2w      = opts.getTransform('voxel', 'world')
            shape    = refImage.shape[:3]
            vlo      = [0, 0, 0]
            vhi      = np.array(shape) - 1
            wlo, whi = transform.axisBounds(shape, v2w)
            wstep    = refImage.pixdim[:3]
        else:
            vlo     = [0, 0, 0]
            vhi     = [0, 0, 0]
            wbounds = self._displayCtx.bounds[:]
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

        if not self or self.destroyed():
            return

        if len(self._overlayList) == 0:      return
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

        if len(self._overlayList) == 0:      return
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

        if len(self._overlayList) == 0:      return
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

        self            .disableNotification('voxelLocation')
        self            .disableNotification('worldLocation')
        self._displayCtx.disableListener(    'location', self._name)

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

        if   source == 'display': coords = self._displayCtx.location.xyz
        elif source == 'voxel':   coords = self.voxelLocation.xyz
        elif source == 'world':   coords = self.worldLocation.xyz

        refImage = self.__registeredOpts.getReferenceImage()

        if refImage is not None:
            opts    = self._displayCtx.getOpts(refImage)
            xformed = opts.transformCoords([coords],
                                           source,
                                           target,
                                           vround=target == 'voxel')[0]
        else:
            xformed = coords

        log.debug('Updating location ({} {} -> {} {})'.format(
            source, coords, target, xformed))

        if   target == 'display': self._displayCtx.location.xyz = xformed
        elif target == 'voxel':   self.voxelLocation       .xyz = xformed
        elif target == 'world':   self.worldLocation       .xyz = xformed


    def __postPropagate(self):
        """Called by the :meth:`__displayLocationChanged`,
        :meth:`__worldLocationChanged` and :meth:`__voxelLocationChanged`
        methods.

        Re-enables the property listeners that were disabled by the
        :meth:`__postPropagate` method.
        """
        self            .enableNotification('voxelLocation')
        self            .enableNotification('worldLocation')
        self._displayCtx.enableListener(    'location', self._name)

        self.Thaw()
        self.Refresh()
        self.Update()


    def __updateLocationInfo(self):
        """Called whenever the :attr:`.DisplayContext.location` changes.
        Updates the HTML panel which displays information about all overlays
        in the :class:`.OverlayList`.
        """

        if len(self._overlayList) == 0 or \
           self.__registeredOverlay is None:
            self.__info.SetPage('')
            return

        # Reverse the overlay order so they
        # are ordered the same on the info
        # page as in the overlay list panel
        overlays = reversed(self._displayCtx.getOrderedOverlays())
        selOvl   = self._displayCtx.getSelectedOverlay()
        lines    = []

        for overlay in overlays:

            display = self._displayCtx.getDisplay(overlay)

            if not display.enabled:
                continue

            info = None
            title = '<b>{}</b>'.format(display.name)

            if not isinstance(overlay, fslimage.Image):
                info = '{}'.format(strings.labels[self, 'noData'])
            else:
                opts = self._displayCtx.getOpts(overlay)
                vloc = opts.getVoxel()

                if vloc is not None:
                    if overlay.is4DImage():
                        vloc = vloc + [opts.volume]

                    vloc = [int(v) for v in vloc]
                    vval = overlay[tuple(vloc)]
                    vloc = ' '.join(map(str, vloc))

                    if not np.isscalar(vval):
                        vval = np.asscalar(vval)

                    if opts.overlayType == 'label':
                        lbl = opts.lut.get(int(vval))
                        if lbl is None: lbl = 'no label'
                        else:           lbl = lbl.name
                        info = '[{}]: {} / {}'.format(vloc, vval, lbl)

                    else:
                        info = '[{}]: {}'.format(vloc, vval)

                else:
                    info = strings.labels[self, 'outOfBounds']

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
    'NiftiOpts'  : ['volume'],
})
"""Different :class:`.DisplayOpts` types have different properties which
affect the current overlay location information.  Therefore, when the current
overlay changes the :meth:`__registerOverlay` method registers property
listeners on the properties specified in this dictionary.
"""
