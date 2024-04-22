#!/usr/bin/env python
#
# lightboxsampl.py - Panel allowing the user to set lightbox slice
#                    settings with voxel indices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxSamplePanel` class. This is a
control panel which allows the user to specify which slices are displayed in
terms of the voxel coordinates of the currently selected image.
"""


import wx

import fsl.data.image                as fslimage
import fsl.utils.idle                as idle
import fsleyes_props                 as props
import fsleyes.strings               as strings
import fsleyes.actions               as actions
import fsleyes.views.lightboxpanel   as lightboxpanel
import fsleyes.controls.controlpanel as ctrlpanel


class LightBoxSampleAction(actions.ToggleControlPanelAction):
    """The ``LightBoxSampleAction`` just toggles a
    :class:`.LightBoxSamplePanel`. It is added as an entry under the FSLeyes
    Tools menu.
    """

    @staticmethod
    def supportedViews():
        """The ``LightBoxSampleAction`` is restricted for use with
        :class:`.LightBoxPanel` views.
        """
        return [lightboxpanel.LightBoxPanel]


    def __init__(self, overlayList, displayCtx, lbpanel):
        """Create a ``LightBoxSampleAction``. """
        super().__init__(overlayList, displayCtx, lbpanel, LightBoxSamplePanel)
        overlayList.listen('overlays', self.name, self.__overlayListChanged)
        self.__overlayListChanged()


    def destroy(self):
        """Called when the :class:`.LightBoxPanel` that owns this action is
        closed. Clears references, removes listeners, and calls the base
        class ``destroy`` method.
        """
        if self.destroyed:
            return
        self.overlayList.removeListener('overlays', self.name)
        super().destroy()


    def __overlayListChanged(self):
        """Called when the selected overlay changes. Enables/disables this
        action (and hence the bound Tools menu item) depending on whether there
        are any images loaded.
        """
        images = [i for i in self.overlayList if isinstance(i, fslimage.Nifti)]
        self.enabled = len(images) > 0


class SliceProperties(props.Props):
    """The ``SliceProperties`` class is used by the
    :class:`LightBoxSamplePanel` to propagate slice settings on to the
    lightbox view - these are ultimately managed by a
    :class:`.LightBoxCanvasOpts` instance.
    """

    image = props.Choice()
    """Currently selected image. """

    zax = props.Choice((0, 1, 2))
    """Current Z axis. """

    sliceStart = props.Int(clamped=True, minval=0, maxval=1)
    """Starting slice in voxels. """

    sliceEnd = props.Int(clamped=True, minval=0, maxval=1)
    """End slice in voxels (inclusive). """

    sliceSpacing = props.Int(clamped=True, minval=0, maxval=1)
    """Spacing between slices in voxels. """

    def __init__(self, lbpanel):
        """Create a ``SliceProperties`` instance.

        :arg lbpanel: The :class:`.LightBoxPanel`
        """

        self.name    = f'{type(self).__name__}_{id(self)}'
        self.lbpanel = lbpanel

        images = lbpanel.overlayList
        images = [i for i in images if isinstance(i, fslimage.Nifti)]

        # The calling code must check whether there are any imagers
        # loaded before attempting to create
        if len(images) == 0:
            raise RuntimeError('Cannot control lightbox slices')

        self.getProp('image').setChoices(images, instance=self)

        opts  = lbpanel.sceneOpts
        dctx  = lbpanel.displayCtx
        image = dctx.getSelectedOverlay()

        if not isinstance(image, fslimage.Nifti):
            image = images[0]

        self.image        = image
        self.zax          = opts.zax
        opts.sampleSlices = 'start'

        self.listen('image',        self.name, self.imageChanged)
        self.listen('zax',          self.name, self.imageChanged)
        self.listen('sliceStart',   self.name, self.refreshLightBox)
        self.listen('sliceEnd',     self.name, self.refreshLightBox)
        self.listen('sliceSpacing', self.name, self.refreshLightBox)
        self.imageChanged()


    def destroy(self):
        """Must be called when this ``SliceProperties`` object is no longer
        needed. Removes listeners and clears references.
        """
        self.lbpanel = None
        self.remove('image',        self.name)
        self.remove('zax',          self.name)
        self.remove('sliceStart',   self.name)
        self.remove('sliceEnd',     self.name)
        self.remove('sliceSpacing', self.name)
        self.getProp('image').setChoices([None], instance=self)


    def imageChanged(self):
        """Called when the :attr:`image` changes. Does the following:

          - Updates limits on the slice properties, and resets them.
          - Updates the :attr:`.DisplayContext.selectedOverlay`
          - Updates the :attr:`.DisplayContext.displaySpace`
          - Calls :meth:`refreshLightBox`
        """

        dctx = self.lbpanel.displayCtx
        img  = self.image
        zax  = self.zax
        zmax = img.shape[zax]

        with props.skip(self,
                        ['sliceStart', 'sliceEnd', 'sliceSpacing'],
                        self.name):
            self.setatt('sliceStart',   'minval', 0)
            self.setatt('sliceEnd',     'minval', 1)
            self.setatt('sliceSpacing', 'minval', 1)
            self.setatt('sliceStart',   'maxval', zmax - 2)
            self.setatt('sliceEnd',     'maxval', zmax - 1)
            self.setatt('sliceSpacing', 'maxval', zmax // 4)
            self.sliceStart   = 0
            self.sliceEnd     = img.shape[zax] - 1
            self.sliceSpacing = 1

        dctx.selectOverlay(img)
        dctx.displaySpace = img
        self.refreshLightBox()


    def refreshLightBox(self):
        """Called when any slices properties have changed.
        Propagates the slice properties on to the corresponding
        properties in the :class:`.LightBoxCanvasOpts` instance.
        """

        lbopts     = self.lbpanel.sceneOpts
        lbopts.zax = self.zax
        lbopts.setSlicesFromVoxels(self.image,
                                   self.sliceStart,
                                   self.sliceEnd,
                                   self.sliceSpacing)


class LightBoxSamplePanel(ctrlpanel.ControlPanel):
    """The ``LightBoxSamplePanel`` allows the user to set up the lightbox
    view in terms of the voxel coordinates of an image. The
    ``LightBoxSamplePanel`` only sets up a GUI - the logic controlling slice
    properties is managed by a :class:`SampleProperties` instance.
    """

    @staticmethod
    def supportedViews():
        """The ``LightBoxSamplePanel`` is restricted for use with
        :class:`.LightBoxPanel` views.
        """
        return [lightboxpanel.LightBoxPanel]


    @staticmethod
    def ignoreControl():
        """Tells the FSLeyes plugin system not to add the
        ``LightBoxSamlpePanel`` as an option to the FSLeyes settings menu.
        Instead, the :class:`LightBoxSampleAction` action is added to the
        tools menu.
        """
        return True


    @staticmethod
    def defaultLayout():
        """Returns a dictionary of arguments to be passed to the
        :meth:`.ViewPanel.togglePanel` method when a ``LightBoxSamplePanel``
        is created.
        """
        return dict(floatPane=True, floatOnly=True)


    def __init__(self, parent, overlayList, displayCtx, lbpanel):
        """Create a ``LightBoxSamplePanel``.

        :arg parent:      ``wx`` parent object
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the
                          :class:`.LightBoxPanel`.
        :arg lbpanel:     The :class:`.LightBoxPanel`.
        """

        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, lbpanel)

        sprops       = SliceProperties(lbpanel)
        self.sprops  = sprops
        self.lbpanel = lbpanel

        def imgLabel(img):
            return img.name

        kwargs  = dict(slider=True, spin=True, showLimits=False)
        start   = props.makeWidget(self, sprops, 'sliceStart',   **kwargs)
        end     = props.makeWidget(self, sprops, 'sliceEnd',     **kwargs)
        spacing = props.makeWidget(self, sprops, 'sliceSpacing', **kwargs)
        image   = props.makeWidget(self, sprops, 'image', labels=imgLabel)
        zax     = props.makeWidget(self, sprops, 'zax',
                                   labels=strings.choices[self, 'zax'])

        ok            = wx.Button(self, wx.ID_OK)
        overview      = wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL)
        imageLabel    = wx.StaticText(self)
        zaxLabel      = wx.StaticText(self)
        startLabel    = wx.StaticText(self)
        endLabel      = wx.StaticText(self)
        spacingLabel  = wx.StaticText(self)

        ok          .SetLabel(strings.labels[self, 'ok'])
        overview    .SetLabel(strings.labels[self, 'overview'])
        imageLabel  .SetLabel(strings.labels[self, 'image'])
        zaxLabel    .SetLabel(strings.labels[self, 'zax'])
        startLabel  .SetLabel(strings.labels[self, 'start'])
        endLabel    .SetLabel(strings.labels[self, 'end'])
        spacingLabel.SetLabel(strings.labels[self, 'spacing'])

        sizer       = wx.BoxSizer(wx.VERTICAL)
        widgetSizer = wx.FlexGridSizer(5, 2, 0, 0)

        widgetSizer.Add(imageLabel,   flag=wx.ALL,    border=3)
        widgetSizer.Add(image,        flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(zaxLabel,     flag=wx.ALL,    border=3)
        widgetSizer.Add(zax,          flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(startLabel,   flag=wx.ALL,    border=3)
        widgetSizer.Add(start,        flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(endLabel,     flag=wx.ALL,    border=3)
        widgetSizer.Add(end,          flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(spacingLabel, flag=wx.ALL,    border=3)
        widgetSizer.Add(spacing,      flag=wx.EXPAND, proportion=1)

        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(overview,    flag=wx.CENTRE, border=10)
        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(widgetSizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(ok,          flag=wx.CENTRE, border=10)
        sizer.Add((1, 10),     flag=wx.EXPAND)

        ok.Bind(wx.EVT_BUTTON, self.onOk)

        self.SetSizer(sizer)
        ok.SetDefault()


    def destroy(self):
        """Must be called when this ``LightBoxSamplePanel`` is no longer
        needed. Clears references and calls the base class ``destroy()``.
        """
        super().destroy()
        idle.idle(self.sprops.destroy)
        self.lbpanel = None
        self.sprops = None


    def onOk(self, ev=None):
        """Called when the "OK" button is pushed. Closes the panel. """
        idle.idle(self.lbpanel.togglePanel, type(self))
