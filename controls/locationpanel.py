#!/usr/bin/env python
#
# locationpanel.py - provides the LocationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LocationPanel` class, a panel which
displays controls allowing the user to change the currently displayed location
in both world and local coordinates, both in the space of the currently
selected overlay.

These changes are propagated to the current display coordinate system
location, managed by the display context (and external changes to the display
context location are propagated back to the local/world location properties
managed by a :class:`LocationPanel`).
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
    """
    A wx.Panel which displays information about the current location,
    for each overlay in the overlay list.
    """

    
    voxelLocation = props.Point(ndims=3, real=False, labels=('X', 'Y', 'Z'))
    """If the currently selected overlay is a :class:`.Image`, this property
    tracks the current display location in voxel coordinates.
    """
    
    worldLocation = props.Point(ndims=3, real=True,  labels=('X', 'Y', 'Z'))

        
    def __init__(self, parent, overlayList, displayCtx):
        """
        Creates and lays out the LocationPanel, and sets up a few property
        event listeners.
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
        self._refImage = None
        
        # When the currently selected overlay is 4D,
        # this attribute will refer to the
        # corresponding DisplayOpts instance, which
        # has a volume property that controls the
        # volume - see e.g. the ImageOpts class. This
        # attribute is set in _selectedOverlayChanged.
        self.volumeTarget = None

        self.column1 = wx.Panel(self)
        self.column2 = wx.Panel(self)
        self.info    = wxhtml.HtmlWindow(self)

        # HTMLWindow does not use
        # the parent font by default,
        # so we force it to at least
        # have the parent font size
        self.info.SetStandardFonts(self.GetFont().GetPointSize())

        self.worldLabel  = wx.StaticText(
            self.column1, label=strings.labels[self, 'worldLocation'])
        self.volumeLabel = wx.StaticText(
            self.column1, label=strings.labels[self, 'volume']) 
        self.voxelLabel  = wx.StaticText(
            self.column2, label=strings.labels[self, 'voxelLocation'])

        worldX, worldY, worldZ = props.makeListWidgets(
            self.column1,
            self,
            'worldLocation',
            slider=False,
            spin=True,
            showLimits=False,
            mousewheel=True)

        voxelX, voxelY, voxelZ = props.makeListWidgets(
            self.column2,
            self,
            'voxelLocation',
            slider=False,
            spin=True,
            showLimits=False,
            mousewheel=True) 

        self.worldX = worldX
        self.worldY = worldY
        self.worldZ = worldZ
        self.voxelX = voxelX
        self.voxelY = voxelY
        self.voxelZ = voxelZ
        self.volume = floatspin.FloatSpinCtrl(
            self.column2,
            style=floatspin.FSC_MOUSEWHEEL | floatspin.FSC_INTEGER)

        self.column1Sizer = wx.BoxSizer(wx.VERTICAL)
        self.column2Sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer        = wx.BoxSizer(wx.HORIZONTAL)

        self.column1Sizer.Add(self.worldLabel,  flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldX,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldY,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldZ,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.volumeLabel, flag=wx.ALIGN_RIGHT)

        self.column2Sizer.Add(self.voxelLabel, flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelX,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelY,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelZ,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.volume,     flag=wx.EXPAND)
        
        self.sizer.Add(self.column1, flag=wx.EXPAND)
        self.sizer.Add((5, -1))
        self.sizer.Add(self.column2, flag=wx.EXPAND)
        self.sizer.Add((5, -1))
        self.sizer.Add(self.info,    flag=wx.EXPAND, proportion=1)

        self.column1.SetSizer(self.column1Sizer)
        self.column2.SetSizer(self.column2Sizer)
        self        .SetSizer(self.sizer)
        
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('location',
                                      self._name,
                                      self._displayLocationChanged)
        self.addListener(             'voxelLocation',
                                      self._name,
                                      self._voxelLocationChanged)
        self.addListener(             'worldLocation',
                                      self._name,
                                      self._worldLocationChanged)

        self._selectedOverlayChanged()

        self.worldLabel.SetMinSize(self.__calcWorldLabelMinSize())
        self.info      .SetMinSize((150, 100))
        self.Layout()
        self.SetMinSize(self.sizer.GetMinSize())


    def __calcWorldLabelMinSize(self):
        """Calculates the minimum size that the world label (the label which
        shows the coordinate space of the currently selected overlay) needs.
        
        The world label displays different things depending on the currently
        selected overlay. But we want it to be a fixed size. So this method
        calculates the size of all possible values that the world label will
        display, and returns the maximum size. This is then used as the
        minimum size for the world label.
        """

        dc = wx.ClientDC(self.worldLabel)

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


    def destroy(self):
        """Deregisters property listeners."""

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        fslpanel.FSLEyesPanel.destroy(self)

        
    def _selectedOverlayChanged(self, *a):
        """Called when the selected overlay is changed. Updates the voxel label
        (which contains the overlay name), and sets the voxel location limits.
        """

        self._updateReferenceImage()
        self._updateWidgets()

        if len(self._overlayList) == 0:
            self._updateLocationInfo()
            return

        # Register a listener on the DisplayOpts 
        # instance of the currently selected overlay,
        # so we can update the location if the
        # overlay transforms/reference image change
        overlay = self._displayCtx.getSelectedOverlay()
        for ovl in self._overlayList:
            display = self._displayCtx.getDisplay(ovl)
            opts    = display.getDisplayOpts()
            
            if ovl is overlay:
                opts.addListener('bounds',
                                 self._name,
                                 self._overlayBoundsChanged,
                                 overwrite=True)
            else:
                opts.removeListener('bounds', self._name)

        # Refresh the world/voxel location properties
        self._displayLocationChanged()


    def _overlayBoundsChanged(self, *a):

        self._updateReferenceImage()
        self._updateWidgets()
        self._displayLocationChanged()
        

    def _updateReferenceImage(self):
        """Called by the :meth:`_selectedOverlayChanged` and
        :meth:`_overlayOptsChanged` methods. Looks at the currently selected
        overlay, and figures out if there is a reference image that can be
        used to transform between display, world, and voxel coordinate
        systems.

        Returns ``True`` if the reference image has changed from its
        previous value, ``False`` otherwise.
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

        self._refImage = refImage
        

    def _updateWidgets(self):

        refImage = self._refImage

        haveRef = refImage is not None

        self.voxelX     .Enable(haveRef)
        self.voxelY     .Enable(haveRef)
        self.voxelZ     .Enable(haveRef)
        self.voxelLabel .Enable(haveRef)

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

        self.worldLabel.SetLabel(label)

        ####################################
        # Voxel/world location widget limits
        ####################################

        # Figure out the limits for the
        # voxel/world location widgets
        if self._refImage is not None:
            opts     = self._displayCtx.getOpts(self._refImage)
            v2w      = opts.getTransform('voxel', 'world')
            shape    = self._refImage.shape[:3]
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
        if self.volumeTarget is not None:
            props.unbindWidget(self.volume,
                               self.volumeTarget,
                               'volume',
                               floatspin.EVT_FLOATSPIN)
            
            self.volumeTarget = None
            self.volume.SetValue(0)
            self.volume.SetRange(0, 0)

        # Enable/disable the volume widget if the
        # overlay is a 4D image, and bind/unbind
        # the widget to the volume property of
        # the associated ImageOpts instance
        if haveRef and refImage.is4DImage():
            opts = self._displayCtx.getOpts(refImage)
            self.volumeTarget = opts

            props.bindWidget(
                self.volume, opts, 'volume', floatspin.EVT_FLOATSPIN)

            self.volume.SetRange(0, refImage.shape[3] - 1)
            self.volume.SetValue(opts.volume)

            self.volume     .Enable()
            self.volumeLabel.Enable()
        else:
            self.volume     .Disable()
            self.volumeLabel.Disable() 

            
    def _prePropagate(self):

        self            .disableNotification('voxelLocation')
        self            .disableNotification('worldLocation')
        self._displayCtx.disableListener(    'location', self._name)

        self.Freeze()

        
    def _propagate(self, source, target):

        if   source == 'display': coords = self._displayCtx.location.xyz
        elif source == 'voxel':   coords = self.voxelLocation.xyz
        elif source == 'world':   coords = self.worldLocation.xyz

        if self._refImage is not None:
            opts    = self._displayCtx.getOpts(self._refImage)
            xformed = opts.transformCoords([coords], source, target)[0]
        else:
            xformed = coords

        log.debug('Updating location ({} {} -> {} {})'.format(
            source, coords, target, xformed))

        if   target == 'display': self._displayCtx.location.xyz = xformed
        elif target == 'voxel':   self.voxelLocation.xyz = np.floor(xformed)
        elif target == 'world':   self.worldLocation.xyz = xformed
        
    
    def _postPropagate(self):
        self            .enableNotification('voxelLocation')
        self            .enableNotification('worldLocation')
        self._displayCtx.enableListener(    'location', self._name)

        self.Thaw()
        self.Refresh()
        self.Update()

    
    def _displayLocationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` changes.
        Propagates the change on to the :attr:`voxelLocation`
        and :attr:`worldLocation` properties.
        """

        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('display', 'voxel')
        self._propagate('display', 'world')
        self._postPropagate()
        self._updateLocationInfo()


    def _worldLocationChanged(self, *a):
        
        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('world', 'voxel')
        self._propagate('world', 'display')
        self._postPropagate()
        self._updateLocationInfo()

        
    def _voxelLocationChanged(self, *a):
        
        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('voxel', 'world')
        self._propagate('voxel', 'display')
        self._postPropagate()
        self._updateLocationInfo()


    def _updateLocationInfo(self):

        if len(self._overlayList) == 0:
            self.info.SetPage('')
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
                
        self.info.SetPage('<br>'.join(lines))
        self.info.Refresh()
