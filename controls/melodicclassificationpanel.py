#!/usr/bin/env python
#
# melodicclassificationpanel.py - The MelodicClassificationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MelodicClassificationPanel` class, a
*FSLeyes control* panel which allows the user to classify the components
of a :class:`.MelodicImage`.
"""


import os
import os.path as op
import logging

import wx

import pwidgets.notebook         as notebook

import fsl.utils.settings        as fslsettings
import fsl.data.strings          as strings
import fsl.data.image            as fslimage
import fsl.data.melodicresults   as fslmelresults
import fsl.data.melodicimage     as fslmelimage
import fsl.fsleyes.colourmaps    as fslcm
import fsl.fsleyes.panel         as fslpanel
import fsl.fsleyes.autodisplay   as autodisplay
import melodicclassificationgrid as melodicgrid


log = logging.getLogger(__name__)


class MelodicClassificationPanel(fslpanel.FSLEyesPanel):
    """The ``MelodicClassificationPanel``
    """

    
    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``MelodicClassificationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """ 
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))


        self.__lut           = fslcm.getLookupTable('melodic-classes')
        self.__notebook      = notebook.Notebook(self)
        self.__componentGrid = melodicgrid.ComponentGrid(
            self.__notebook,
            self._overlayList,
            self._displayCtx,
            self.__lut)

        self.__labelGrid     = melodicgrid.LabelGrid(
            self.__notebook,
            self._overlayList,
            self._displayCtx,
            self.__lut)

        self.__loadButton  = wx.Button(self)
        self.__saveButton  = wx.Button(self)
        self.__clearButton = wx.Button(self)

        self.__notebook.AddPage(self.__componentGrid,
                                strings.labels[self, 'componentTab'])
        self.__notebook.AddPage(self.__labelGrid,
                                strings.labels[self, 'labelTab'])

        self.__loadButton .SetLabel(strings.labels[self, 'loadButton'])
        self.__saveButton .SetLabel(strings.labels[self, 'saveButton'])
        self.__clearButton.SetLabel(strings.labels[self, 'clearButton'])

        # Things which you don't want shown when
        # a melodic image is not selected should
        # be added to __mainSizer. Things which
        # you always want displayed should be
        # added to __sizer (but need to be laid
        # out w.r.t. __disabledText/__mainSizer)
 
        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer     = wx.BoxSizer(wx.VERTICAL)

        self.__btnSizer .Add(self.__loadButton,   flag=wx.EXPAND, proportion=1)
        self.__btnSizer .Add(self.__saveButton,   flag=wx.EXPAND, proportion=1)
        self.__btnSizer .Add(self.__clearButton,  flag=wx.EXPAND, proportion=1)
        
        self.__mainSizer.Add(self.__notebook,     flag=wx.EXPAND, proportion=1)

        self.__sizer    .Add(self.__disabledText, flag=wx.EXPAND, proportion=1)
        self.__sizer    .Add(self.__mainSizer,    flag=wx.EXPAND, proportion=1)
        self.__sizer    .Add(self.__btnSizer,     flag=wx.EXPAND)

        self.SetSizer(self.__sizer)

        self.__loadButton .Bind(wx.EVT_BUTTON, self.__onLoadButton)
        self.__saveButton .Bind(wx.EVT_BUTTON, self.__onSaveButton)
        self.__clearButton.Bind(wx.EVT_BUTTON, self.__onClearButton)

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()

        self.SetMinSize((400, 100))


    def destroy(self):
        """
        """
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__componentGrid.destroy()
        self.__labelGrid    .destroy()
        
        fslpanel.FSLEyesPanel.destroy(self)


    def __enable(self, enable=True, message=''):
        """
        """

        self.__disabledText.SetLabel(message)
        
        self.__sizer.Show(self.__disabledText, not enable)
        self.__sizer.Show(self.__mainSizer,    enable)

        self.__saveButton .Enable(enable)
        self.__clearButton.Enable(enable)

        self.Layout()


    def __selectedOverlayChanged(self, *a):
        """
        """

        overlay = self._displayCtx.getSelectedOverlay()

        self.__componentGrid.setOverlay(overlay)
        self.__labelGrid    .setOverlay(overlay)

        if (overlay is None) or \
           not isinstance(overlay, fslmelimage.MelodicImage):
            self.__enable(False, strings.messages[self, 'disabled'])
            return

        self.__enable(True)

        
    def __onLoadButton(self, ev):
        """Called when the *Load labels* button is pushed.  Prompts the user
        to select a label file to load, then does the following:

        1. If the selected label file refers to the currently selected
           melodic_IC overlay, the labels are applied to the overlay.

        2. If the selected label file refers to a different melodic_IC
           overlay, the user is asked whether they want to load the
           different melodic_IC file (the default), or whether they
           want the labels applied to the existing overlay.

        3. If the selected label file does not refer to any overlay
           (it only contains the bad component list), the user is asked
           whether they want the labels applied to the current melodic_IC
           overlay.

        If the number of labels in the file is less than the number of
        melodic_IC components, thew remaining components are labelled
        as unknown. If the number of labels in the file is greater than
        the number of melodic_IC components, an error is shown, and
        nothing is done.
        """

        # The aim of the code beneath this function
        # is to load a set of component labels, and
        # to figure out which overlay they should
        # be added to. When it has done this, it
        # calls this function.
        def applyLabels(labelFile, overlay, allLabels):

            lut      = self.__lut
            melclass = overlay.getICClassification()

            ncomps  = overlay.numComponents()
            nlabels = len(allLabels)

            # Error: number of labels in the
            # file is greater than the number
            # of components in the overlay.
            if ncomps < nlabels:
                msg   = strings.messages[self, 'wrongNComps'].format(
                    labelFile, overlay.dataSource)
                title = strings.titles[  self, 'loadError']
                wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)                
                return

            # Number of labels in the file is
            # less than number of components
            # in the overlay - we pad the
            # labels with 'Unknown'
            elif ncomps > nlabels:
                for i in range(nlabels, ncomps):
                    allLabels.append(['Unknown'])

            # Disable notification while applying
            # labels so the component/label grids
            # don't confuse themselves. We'll
            # manually refresh them below.
            melclass.disableNotification('labels')
            lut     .disableNotification('labels')

            melclass.clear()

            for comp, lbls in enumerate(allLabels):
                for lbl in lbls:
                    melclass.addLabel(comp, lbl)

            # Make sure a colour in the melodic
            # lookup table exists for all labels
            for comp, labels in enumerate(melclass.labels):
                for label in labels:

                    label    = melclass.getDisplayLabel(label)
                    lutLabel = lut.getByName(label)

                    if lutLabel is None:
                        log.debug('New melodic classification '
                                  'label: {}'.format(label))
                        lut.new(label)

            melclass.enableNotification('labels') 
            lut     .enableNotification('labels')

            # If we have just loaded a MelodicImage,
            # make sure it is selected. If we loaded
            # labels for an existing MelodicImage,
            # this will have no effect.
            self._displayCtx.disableListener('selectedOverlay', self._name)
            self._displayCtx.selectOverlay(overlay)
            self._displayCtx.enableListener('selectedOverlay', self._name)
            self.__selectedOverlayChanged()

        # If the current overlay is a MelodicImage,
        # the open file dialog starting point will
        # be the melodic directory.
        overlay           = self._displayCtx.getSelectedOverlay()
        selectedIsMelodic = isinstance(overlay, fslmelimage.MelodicImage)
        
        if selectedIsMelodic:
            loadDir = overlay.getMelodicDir()

        # Otherwise it will be the most
        # recent overlay load directory.
        else:
            loadDir = fslsettings.read('loadOverlayLastDir', os.getcwd())

        # Ask the user to select a label file
        dlg = wx.FileDialog(
            self,
            message=strings.titles[self, 'loadDialog'],
            defaultDir=loadDir,
            style=wx.FD_OPEN)

        # User cancelled the dialog
        if dlg.ShowModal() != wx.ID_OK:
            return

        # Load the specified label file
        filename = dlg.GetPath()
        try:
            melDir, allLabels = fslmelresults.loadMelodicLabelFile(filename)

        # Problem loading the file
        except Exception as e:
            
            e     = str(e)
            msg   = strings.messages[self, 'loadError'].format(filename, e)
            title = strings.titles[  self, 'loadError']
            log.debug('Error loading classification file '
                      '({}), ({})'.format(filename, e), exc_info=True)
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)

            return

        # Ok we've got the labels, now
        # we need to figure out which
        # overlay to add them to.

        # If the label file does not refer
        # to a Melodic directory, and the
        # current overlay is a melodic
        # image, apply the labels to the image.
        if selectedIsMelodic and (melDir is None):
            applyLabels(filename, overlay, allLabels)
            return

        # If the label file refers to a
        # Melodic directory, and the
        # current overlay is a melodic
        # image.
        if selectedIsMelodic and (melDir is not None):

            overlayDir = overlay.getMelodicDir()

            # And both the current overlay and
            # the label file refer to the same
            # melodic directory, then we apply
            # the labels to the curent overlay.
            if op.abspath(melDir) == op.abspath(overlayDir):

                applyLabels(filename, overlay, allLabels)
                return
            
            # Otherwise, if the overlay and the
            # label file refer to different
            # melodic directories...

            # Ask the user whether they want to
            dlg = wx.MessageDialog(
                self,
                strings.messages[self, 'diffMelDir'].format(
                    melDir, overlayDir),
                style=wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
            dlg.SetYesNoLabels(
                strings.messages[self, 'diffMelDir.labels'],
                strings.messages[self, 'diffMelDir.overlay'])

            response = dlg.ShowModal()

            # User cancelled the dialog
            if response == wx.ID_CANCEL:
                return

            # User chose to load the melodic
            # image specified in the label
            # file. We'll carry on with this
            # processing below.
            elif response == wx.ID_YES:
                pass

            # Apply the labels to the current
            # overlay, even though they are
            # from different analyses.
            else:
                applyLabels(filename, overlay, allLabels)
                return

        # If we've reached this far, we are
        # going to attempt to identify the
        # melodic image associated with the
        # label file, load that image, and
        # then apply the labels.
        
        # The label file does not
        # specify a melodic directory
        if melDir is None:

            msg   = strings.messages[self, 'noMelDir'].format(filename)
            title = strings.titles[  self, 'loadError']
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)
            return

        # Try loading the melodic_IC image
        # specified in the label file. We'll
        # load the mean image as well, as an
        # underlay.
        try:
            overlay = fslmelimage.MelodicImage( melDir)
            mean    = fslmelresults.getMeanFile(melDir)
            mean    = fslimage.Image(           mean)

            log.debug('Adding {} and {} to overlay list'.format(overlay, mean))

            self._overlayList.disableListener('overlays', self._name)
            self._displayCtx .disableListener('selectedOverlay', self._name)
            self._overlayList.extend([mean, overlay])
            self._overlayList.enableListener('overlays', self._name)
            self._displayCtx .enableListener('selectedOverlay', self._name)

            if self._displayCtx.autoDisplay:
                for o in [overlay, mean]:
                    autodisplay.autoDisplay(o,
                                            self._overlayList,
                                            self._displayCtx)

            fslsettings.write('loadOverlayLastDir', op.abspath(melDir)) 

        except Exception as e:

            e     = str(e)
            msg   = strings.messages[self, 'loadError'].format(filename, e)
            title = strings.titles[  self, 'loadError']
            log.debug('Error loading classification file '
                      '({}), ({})'.format(filename, e), exc_info=True)
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)

        # Apply the loaded labels
        # to the loaded overlay.
        applyLabels(filename, overlay, allLabels)

    
    def __onSaveButton(self, ev):
        """
        """
        overlay  = self._displayCtx.getSelectedOverlay()
        melclass = overlay.getICClassification()
        dlg      = wx.FileDialog(
            self,
            message=strings.titles[self, 'saveDialog'],
            defaultDir=overlay.getMelodicDir(),
            style=wx.FD_SAVE)
        
        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()

        try:
            melclass.save(filename)
            
        except Exception as e:
            e     = str(e)
            msg   = strings.messages[self, 'saveError'].format(filename, e)
            title = strings.titles[  self, 'saveError']
            log.debug('Error saving classification file '
                      '({}), ({})'.format(filename, e), exc_info=True)
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 

    
    def __onClearButton(self, ev):
        """
        """
        
        overlay  = self._displayCtx.getSelectedOverlay()
        melclass = overlay.getICClassification()

        melclass.clear()

        melclass.disableNotification('labels')
        
        for c in range(overlay.numComponents()):
            melclass.addLabel(c, 'Unknown')
            
        melclass.enableNotification('labels')
        melclass.notify('labels')
