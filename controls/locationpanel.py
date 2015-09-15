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

import wx
import wx.html as wxhtml

import numpy as np

import props

import pwidgets.floatspin  as floatspin

import fsl.utils.transform as transform
import fsl.data.image      as fslimage
import fsl.data.constants  as constants
import fsl.data.strings    as strings
import fsl.fsleyes.panel   as fslpanel


log = logging.getLogger(__name__)


class LocationPanel(fslpanel.FSLEyesPanel):
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

        
    def __init__(self, parent, overlayList, displayCtx):
        """Creat a ``LocationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        # The world and voxel locations dispalyed by the LocationPanel
        # are only really relevant to volumetric (i.e. NIFTI) overlay
        # types. However, other overlay types (e.g. Model instances)
        # may have an associated 'reference' image, from which details
        # of the coordinate system may be obtained.
        #
        # When the current overlay is either an Image instance, or has
        # an associated reference image, this attributes is used to
        # store a reference to the image.
        self.__refImage = None
        
        # When the currently selected overlay is 4D,
        # this attribute will refer to the
        # corresponding DisplayOpts instance, which
        # has a volume property that controls the
        # volume - see e.g. the ImageOpts class. This
        # attribute is set in _selectedOverlayChanged.
        self.__volumeTarget = None

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

        self.__worldLabel.SetMinSize(self.__calcWorldLabelMinSize())
        self.__info      .SetMinSize((150, 100))
        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called when this ``LocationPanel`` is no longer needed.
        Removes property listeners and calls :meth:`.FSLEyesPanel.destroy`.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        fslpanel.FSLEyesPanel.destroy(self)


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
            strings.anatomy[fslimage.Image,
                            'space',
                            constants.NIFTI_XFORM_UNKNOWN],
            strings.anatomy[fslimage.Image,
                            'space',
                            constants.NIFTI_XFORM_SCANNER_ANAT],
            strings.anatomy[fslimage.Image,
                            'space',
                            constants.NIFTI_XFORM_ALIGNED_ANAT],
            strings.anatomy[fslimage.Image,
                            'space',
                            constants.NIFTI_XFORM_TALAIRACH],
            strings.anatomy[fslimage.Image,
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
        :class:`.OverlayList` is changed. Refreshes the ``LocationPanel``
        interface accordingly.
        """

        self.__updateReferenceImage()
        self.__updateWidgets()

        if len(self._overlayList) == 0:
            self.__updateLocationInfo()
            return

        # Register a listener on the DisplayOpts 
        # instance of the currently selected overlay,
        # so we can update the location if the
        # overlay bounds change.
        overlay = self._displayCtx.getSelectedOverlay()
        for ovl in self._overlayList:
            display = self._displayCtx.getDisplay(ovl)
            opts    = display.getDisplayOpts()
            
            if ovl is overlay:
                opts.addListener('bounds',
                                 self._name,
                                 self.__overlayBoundsChanged,
                                 overwrite=True)
            else:
                opts.removeListener('bounds', self._name)

        # Refresh the world/voxel location properties
        self.__displayLocationChanged()


    def __overlayBoundsChanged(self, *a):
        """Called when the :attr:`.DisplayOpts.bounds` property associated
        with the currently selected overlay changes. Updates the
        ``LocationPanel`` interface accordingly.
        """

        self.__updateReferenceImage()
        self.__updateWidgets()
        self.__displayLocationChanged()
        

    def __updateReferenceImage(self):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__overlayBoundsChanged` methods. Looks at the currently
        selected overlay, and figures out if there is a reference image
        that can be used to transform between display, world, and voxel
        coordinate systems.
        """

        refImage = None
        
        # Look at the currently selected overlay, and
        # see if there is an associated NIFTI image
        # that can be used as a reference image
        if len(self._overlayList) > 0:

            overlay  = self._displayCtx.getSelectedOverlay()
            refImage = self._displayCtx.getReferenceImage(overlay)

            log.debug('Reference image for overlay {}: {}'.format(
                overlay, refImage))

        self.__refImage = refImage
        

    def __updateWidgets(self):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__overlayBoundsChanged` methods.  Enables/disables the
        voxel/world location and volume controls depending on the currently
        selected overlay (or reference image).
        """

        refImage = self.__refImage

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
        else:
            vlo     = [0, 0, 0]
            vhi     = [0, 0, 0]
            wbounds = self._displayCtx.bounds[:]
            wlo     = wbounds[0::2]
            whi     = wbounds[1::2]

        # Update the voxel and world location limits,
        # but don't trigger a listener callback, as
        # this would change the display location.
        self.disableNotification('worldLocation')
        self.disableNotification('voxelLocation')

        log.debug('Setting voxelLocation limits: {} - {}'.format(vlo, vhi))
        log.debug('Setting worldLocation limits: {} - {}'.format(wlo, whi))

        for i in range(3):
            self.voxelLocation.setLimits(i, vlo[i], vhi[i])
            self.worldLocation.setLimits(i, wlo[i], whi[i])
            
        self.enableNotification('worldLocation')
        self.enableNotification('voxelLocation')

        ###############
        # Volume widget
        ###############

        # Unbind any listeners between the previous
        # reference image and the volume widget
        if self.__volumeTarget is not None:
            props.unbindWidget(self.__volume,
                               self.__volumeTarget,
                               'volume',
                               floatspin.EVT_FLOATSPIN)
            
            self.__volumeTarget = None
            self.__volume.SetValue(0)
            self.__volume.SetRange(0, 0)

        # Enable/disable the volume widget if the
        # overlay is a 4D image, and bind/unbind
        # the widget to the volume property of
        # the associated ImageOpts instance
        if haveRef and refImage.is4DImage():
            opts = self._displayCtx.getOpts(refImage)
            self.__volumeTarget = opts

            props.bindWidget(
                self.__volume, opts, 'volume', floatspin.EVT_FLOATSPIN)

            self.__volume.SetRange(0, refImage.shape[3] - 1)
            self.__volume.SetValue(opts.volume)

            self.__volume     .Enable()
            self.__volumeLabel.Enable()
        else:
            self.__volume     .Disable()
            self.__volumeLabel.Disable() 

            
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

        if len(self._overlayList) == 0: return

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
        
        if len(self._overlayList) == 0: return

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
        
        if len(self._overlayList) == 0: return

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

        if self.__refImage is not None:
            opts    = self._displayCtx.getOpts(self.__refImage)
            xformed = opts.transformCoords([coords], source, target)[0]
        else:
            xformed = coords

        log.debug('Updating location ({} {} -> {} {})'.format(
            source, coords, target, xformed))

        if   target == 'display': self._displayCtx.location.xyz = xformed
        elif target == 'voxel':   self.voxelLocation.xyz = np.floor(xformed)
        elif target == 'world':   self.worldLocation.xyz = xformed
        
    
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

        if len(self._overlayList) == 0:
            self.__info.SetPage('')
            return

        overlays = self._displayCtx.getOrderedOverlays()
        selOvl   = self._displayCtx.getSelectedOverlay()
        
        overlays.remove(selOvl)
        overlays.insert(0, selOvl)

        lines = []
        for overlay in overlays:

            display = self._displayCtx.getDisplay(overlay)
            
            if not display.enabled:
                continue

            title = '<b>{}</b>'.format(overlay.name)
            info  = None

            if not isinstance(overlay, fslimage.Image):
                info = '{}'.format(strings.labels[self, 'noData'])
            else:
                opts = self._displayCtx.getOpts(overlay)
                vloc = opts.transformCoords(
                    [self._displayCtx.location.xyz], 'display', 'voxel')[0]

                vloc = tuple(map(int, np.floor(vloc)))

                if overlay.is4DImage():
                    vloc = vloc + (opts.volume,)

                inBounds = True
                for i in range(3):
                    if vloc[i] < 0 or vloc[i] >= overlay.shape[i]:
                        inBounds = False

                if inBounds:
                    vval = overlay.data[vloc]
                    info = '[{}]: {}'.format(' '.join(map(str, vloc)), vval)
                else:
                    info = strings.labels[self, 'outOfBounds']

            lines.append(title)
            if info is not None:
                lines.append(info)
                
        self.__info.SetPage('<br>'.join(lines))
        self.__info.Refresh()
