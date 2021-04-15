#!/usr/bin/env python
#
# addmaskdataseries.py - The AddMaskDataSeriesAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AddMaskDataSeriesAction` class, an action
used by the :class:`.TimeSeriesPanel`.
"""


import          wx
import numpy as np

import fsl.data.image                as fslimage

import fsleyes.strings               as strings
import fsleyes.plotting.dataseries   as dataseries
import fsleyes.views.timeseriespanel as timeseriespanel
import fsleyes.actions.base          as base


class AddMaskDataSeriesAction(base.Action):
    """The ``AddMaskDataSeriesAction`` class is used by the
    :class:`.TimeSeriesPanel`.

    It prompts the user to select a mask image for the currently selected
    overlay (assumed to be a 4D time series :class:`.Image`), then extracts
    the mean time series for the non-zero voxels within the mask, and adds
    them as a :class:`.DataSeries` to the ``TimeSeriesPanel``.
    """


    @staticmethod
    def supportedViews():
        """The ``AddMaskDataSeriesAction`` is restricted for use with
        :class:`.TimeSeriesPanel` views.
        """
        return [timeseriespanel.TimeSeriesPanel]


    def __init__(self, overlayList, displayCtx, plotPanel):
        """Create an ``AddMaskDataSeriesAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg plotPanel:   The :class:`.TimeSeriesPanel`.
        """

        base.Action.__init__(
            self, overlayList, displayCtx, self.__addMaskDataSeries)

        self.__plotPanel   = plotPanel
        self.__maskOptions = []

        overlayList.addListener('overlays',
                                self.name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__overlayListChanged)

        self.__overlayListChanged()


    def destroy(self):
        """Must be called when this ``AddMaskDataSeriesAction`` is no
        longer in use.
        """
        if self.destroyed:
            return
        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.__plotPanel   = None
        self.__maskOptions = None
        base.Action.destroy(self)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Updates the
        :attr:`.Action.enabled` flag based on the currently selected
        overlay, and the contents of the overlay list.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if (len(self.overlayList) == 0 or
           (not isinstance(overlay, fslimage.Image))):
            self.enabled = False
            return

        self.__maskOptions = [o for o in self.overlayList if
                              isinstance(o, fslimage.Image) and
                              o is not overlay              and
                              o.sameSpace(overlay)]

        self.enabled = (overlay.ndim > 3 and len(self.__maskOptions) > 0)


    def __addMaskDataSeries(self):
        """Run the ``AddMaskDataSeriesAction``. Prompt the user to select
        a mask, using a :class:`MaskDialog`, then calculates the mean time
        series in that mask, then adds that time series to the
        :class:`.TimeSeriesPanel` that owns this action instance.
        """

        overlay = self.displayCtx.getSelectedOverlay()
        opts    = self.displayCtx.getOpts(overlay)
        options = self.__maskOptions

        frame   = wx.GetApp().GetTopWindow()
        msg     = strings.messages[self, 'selectMask'].format(overlay.name)
        cbmsg   = strings.messages[self, 'weighted']
        title   = strings.titles[  self, 'selectMask'].format(overlay.name)

        dlg = MaskDialog(
            frame,
            [o.name for o in options],
            title=title,
            message=msg,
            checkboxMessage=cbmsg)

        if dlg.ShowModal() != wx.ID_OK:
            return

        maskimg   = options[dlg.GetChoice()]
        weight    = dlg.GetCheckBox()
        ds        = dataseries.DataSeries(overlay,
                                          self.overlayList,
                                          self.displayCtx,
                                          self.__plotPanel)

        data     = overlay.data[opts.index(atVolume=False)]
        mask     = maskimg.data
        maskmask = mask > 0
        ydata    = data[maskmask]

        # Weighted mean
        if weight:
            maskvals = mask[maskmask]
            ydata    = (maskvals * ydata.T).T

        ydata = ydata.mean(axis=0)
        xdata = np.arange(len(ydata))

        ds.colour    = self.__plotPanel.getOverlayPlotColour(overlay)
        ds.lineStyle = self.__plotPanel.getOverlayPlotStyle(overlay)
        ds.lineWidth = 2
        ds.alpha     = 1
        ds.label     = '{} [mask: {}]'.format(overlay.name, maskimg.name)

        # We have to run the data through
        # prepareDataSeries to e.g. scale
        # the x axis by pixdims, and apply
        # other plot settings
        ds.setData(xdata, ydata)
        ds.setData(*self.__plotPanel.prepareDataSeries(ds))

        self.__plotPanel.canvas.dataSeries.append(ds)



class MaskDialog(wx.Dialog):
    """A dialog which displays some options to the user:

     - A ``Choice`` widget containing a list of mask images
     - A checkbox allowing the user to select whether to calculate
       the weighted mean time series, weighted by the mask values,
       or calculate the unweighted mean.

    The selections are available via the :meth:`GetMask` and
    :meth:`GetWeighted` methods
    """

    def __init__(self,
                 parent,
                 choices,
                 title=None,
                 message=None,
                 checkbox=True,
                 checkboxMessage=None):
        """Create a ``ChoiceDialog``.

        :arg parent:          ``wx`` parent object.
        :arg choices:         List of strings, the choices to present to the
                              user.
        :arg title:           Dialog title
        :arg message:         Message to show above choice widget.
        :arg checkbox:        Show a checkbox
        :arg checkboxMessage: Message to show alongside checkbox widget.
        """

        if title           is None: title           = ''
        if message         is None: message         = ''
        if checkboxMessage is None: checkboxMessage = ''

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.__message      = wx.StaticText(self, label=message)
        self.__choice       = wx.Choice(self,     choices=choices)

        if checkbox: self.__checkbox = wx.CheckBox(self, label=checkboxMessage)
        else:        self.__checkbox = None

        self.__okButton     = wx.Button(self, label='Ok',     id=wx.ID_OK)
        self.__cancelButton = wx.Button(self, label='Cancel', id=wx.ID_CANCEL)

        self.__okButton    .Bind(wx.EVT_BUTTON, self.__onOkButton)
        self.__cancelButton.Bind(wx.EVT_BUTTON, self.__onCancelButton)

        self.__okButton.SetDefault()

        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)
        self.__buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__buttonSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__okButton)
        self.__buttonSizer.Add((5, 1), flag=wx.EXPAND)
        self.__buttonSizer.Add(self.__cancelButton)

        self.__mainSizer.Add(self.__message,
                             flag=wx.EXPAND | wx.ALL,
                             proportion=1,
                             border=20)
        self.__mainSizer.Add(self.__choice,
                             flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                             border=20)

        if checkbox:
            self.__mainSizer.Add(self.__checkbox,
                                 flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
                                 border=20)

        self.__mainSizer.Add(self.__buttonSizer,
                             flag=wx.EXPAND | wx.ALL,
                             border=20)

        self.SetSizer(self.__mainSizer)
        self.Layout()
        self.Fit()
        self.CentreOnParent()


    @property
    def okButton(self):
        """Returns the OK button. """
        return self.__okButton


    @property
    def cancelButton(self):
        """Returns the cancel button. """
        return self.__cancelButton


    @property
    def checkbox(self):
        """Returns the checkbox. """
        return self.__checkbox


    @property
    def choice(self):
        """Returns the choice widget. """
        return self.__choice


    def GetChoice(self):
        """Returns the index of the currently selected choice."""
        return self.__choice.GetSelection()


    def GetCheckBox(self):
        """Returns the index of the currently selected choice."""
        if self.__checkbox is None:
            raise RuntimeError('This dialog does not have a checkbox')

        return self.__checkbox.GetValue()


    def __onOkButton(self, ev):
        """Called when the ok button is pushed. """
        self.EndModal(wx.ID_OK)


    def __onCancelButton(self, ev):
        """Called when the cancel button is pushed. """
        self.EndModal(wx.ID_CANCEL)
