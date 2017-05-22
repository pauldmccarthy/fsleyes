#!/usr/bin/env python
#
# lookuptablepanel.py - The LookupTablePanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LookupTablePanel`, a *FSLeyes control*
panel which allows the user to manage lookup tables. See the
:mod:`.colourmaps` module for more details on lookup tables.

A few other classes and functions are defined in this module, all for use by
the ``LookupTablePanel``:

.. autosummary::
   :nosignatures:

   promptForLutName
   LabelWidget
   LutLabelDialog
"""


import            os
import os.path as op
import            logging

import wx

import fsl.utils.async              as async
import fsl.utils.settings           as fslsettings
import fsl.data.melodicimage        as fslmelimage

import fsleyes_props                as props
import fsleyes_widgets.elistbox     as elistbox
import fsleyes_widgets.utils.status as status

import fsleyes.panel                as fslpanel
import fsleyes.displaycontext       as displayctx
import fsleyes.colourmaps           as fslcmaps
import fsleyes.strings              as strings



log = logging.getLogger(__name__)


class LookupTablePanel(fslpanel.FSLeyesPanel):
    """A ``LookupTablePanel`` is a :class:`.FLSEyesPanel` which allows users
    to manage ``LookupTable`` instances. A ``LookupTablePanel`` looks
    something like this:

    .. image:: images/lookuptablepanel.png
       :scale: 50%
       :align: center


    A ``LookupTablePanel`` allows the user to do the following:

      - Add/remove labels to/from a :class:`LookupTable`.

      - Change the colour, name, and visibility of a label in a
        ``LookupTable``.

      - Create a new ``LookupTable``, or copy an existing one.

      - Save/load a ``LookupTable`` to/from a file.


    The ``LookupTablePanel`` keeps track of the currently selected overlay
    (see the :attr:`.DisplayContext.selectedOverlay` property). If the overlay
    is associated with a :class:`.LabelOpts` instance, its
    :attr:`.Labelopts.lut` property will be updated when the
    :class:`LookupTable` is changed through the ``LookupTablePanel``, and vice
    versa.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``LookupTablePanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__controlCol = wx.Panel(self)
        self.__labelList  = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE   |
                         elistbox.ELB_NO_ADD    |
                         elistbox.ELB_NO_REMOVE |
                         elistbox.ELB_WIDGET_RIGHT))

        self.__lutChoice       = wx.Choice(self.__controlCol)
        self.__selAllButton    = wx.Button(self.__controlCol)
        self.__selNoneButton   = wx.Button(self.__controlCol)
        self.__addLabelButton  = wx.Button(self.__controlCol)
        self.__rmLabelButton   = wx.Button(self.__controlCol)
        self.__newLutButton    = wx.Button(self.__controlCol)
        self.__copyLutButton   = wx.Button(self.__controlCol)
        self.__saveLutButton   = wx.Button(self.__controlCol)
        self.__loadLutButton   = wx.Button(self.__controlCol)

        self.__controlColSizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer           = wx.BoxSizer(wx.VERTICAL)

        self.__controlCol.SetSizer(self.__controlColSizer)
        self             .SetSizer(self.__sizer)

        self.__controlColSizer.Add(self.__lutChoice,      flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__selAllButton,   flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__selNoneButton,  flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__addLabelButton, flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__rmLabelButton,  flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__newLutButton,   flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__copyLutButton,  flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__loadLutButton,  flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__saveLutButton,  flag=wx.EXPAND)

        self.__sizer.Add(self.__controlCol, flag=wx.EXPAND)
        self.__sizer.Add(self.__labelList,  flag=wx.EXPAND, proportion=1)

        # Label the buttons
        self.__selAllButton  .SetLabel(strings.labels[  self, 'selectAll'])
        self.__selNoneButton .SetLabel(strings.labels[  self, 'selectNone'])
        self.__addLabelButton.SetLabel(strings.labels[  self, 'addLabel'])
        self.__rmLabelButton .SetLabel(strings.labels[  self, 'removeLabel'])
        self.__newLutButton  .SetLabel(strings.labels[  self, 'newLut'])
        self.__copyLutButton .SetLabel(strings.labels[  self, 'copyLut'])
        self.__loadLutButton .SetLabel(strings.labels[  self, 'loadLut'])
        self.__saveLutButton .SetLabel(strings.labels[  self, 'saveLut'])

        self.__lutChoice     .Bind(wx.EVT_CHOICE, self.__onLutChoice)
        self.__selAllButton  .Bind(wx.EVT_BUTTON, self.__onSelectAll)
        self.__selNoneButton .Bind(wx.EVT_BUTTON, self.__onSelectNone)
        self.__addLabelButton.Bind(wx.EVT_BUTTON, self.__onLabelAdd)
        self.__rmLabelButton .Bind(wx.EVT_BUTTON, self.__onLabelRemove)
        self.__newLutButton  .Bind(wx.EVT_BUTTON, self.__onNewLut)
        self.__copyLutButton .Bind(wx.EVT_BUTTON, self.__onCopyLut)
        self.__loadLutButton .Bind(wx.EVT_BUTTON, self.__onLoadLut)
        self.__saveLutButton .Bind(wx.EVT_BUTTON, self.__onSaveLut)

        # The selected overlay / DisplayOpts
        # are tracked if they use an LUT
        # (e.g. LabelOpts). And the currently
        # selected/displayed LUT is always
        # tracked.
        self.__selectedOverlay = None
        self.__selectedOpts    = None
        self.__selectedLut     = None

        # See the __createLabelList method
        self.__labelListCreateKey = 0

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__updateLutChoices()
        self.__selectedOverlayChanged()

        # If the selected lut was not set
        # via the selectedOverlayChanged
        # call, we'll manually set it here
        if self.__selectedLut is None:
            self.__setLut(fslcmaps.getLookupTables()[0])

        self.Layout()

        # The label values (used as labels in the
        # EditableListBox) seem to get squashed
        # easily. So we're adding a bit of padding
        # to force this panel to have a minimum
        # size, to ensure that the labels are
        # visible.
        dc      = wx.ClientDC(self.__labelList)
        w, h    = dc.GetTextExtent('9999')
        minSize = self.__sizer.GetMinSize()
        self.SetMinSize((minSize[0] + w, minSize[1]))


    def destroy(self):
        """Must be called when this ``LookupTablePanel`` is no longer needed.
        Removes some property listeners, and calls the
        :meth:`FSLeyesPanel.destroy` method.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        overlay = self.__selectedOverlay
        opts    = self.__selectedOpts
        lut     = self.__selectedLut

        if overlay is not None and overlay in self._overlayList:

            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('overlayType', self._name)

        if opts is not None:
            opts.removeListener('lut', self._name)

        if lut is not None:
            lut.deregister(self._name, 'saved')
            lut.deregister(self._name, 'added')
            lut.deregister(self._name, 'removed')

        self.__selectedOverlay = None
        self.__selectedOpts    = None
        self.__selectedLut     = None

        fslpanel.FSLeyesPanel.destroy(self)


    def __updateLutChoices(self):
        """Refreshes the contents of the lookup table drop down box,
        using the :class:`.LookupTable` instances returned by the
        :func:`.colourmaps.getLookupTables` function.
        """

        log.debug('Updating lookup table choices')

        oldNames     = self.__lutChoice.GetItems()
        oldSelection = self.__lutChoice.GetSelection()

        luts     = fslcmaps.getLookupTables()
        newNames = [l.name for l in luts]

        try:    newSelection = oldNames.index(oldNames[oldSelection])
        except: newSelection = 0

        self.__lutChoice.SetItems(newNames)
        self.__lutChoice.SetSelection(newSelection)

        for i, lut in enumerate(luts):
            self.__lutChoice.SetClientData(i, lut)


    def __createLabelList(self):
        """Refreshes the contents of the class:`.LookupTable` label list, from
        the currently selected ``LookupTable``.
        """

        # The label list is created asynchronously on
        # the wx.Idle loop, because it can take some
        # time for big lookup tables. In the event
        # that the list needs to be re-created (e.g.
        # the current lookup table is changed), this
        # attribute is used so that scheduled creation
        # routines (the addLabel function defined
        # below) can tell whether they should cancel.
        myCreateKey = (self.__labelListCreateKey + 1) % 65536
        self.__labelListCreateKey = myCreateKey

        lut     = self.__selectedLut
        nlabels = len(lut)

        self.__labelList.Clear()

        # If this is a new lut, it
        # won't have any labels
        if nlabels == 0:
            return

        # The label widgets are created via consecutive
        # calls to addLabel, which is scheduled on the
        # async.idle loop. We create blockSize labels
        # in each asynchronous call.
        blockSize = 100

        def addLabel(startIdx):

            # If the user closes this panel while the
            # label list is being created, wx will
            # complain when we try to append things
            # to a widget that has been destroyed.
            try:

                for labelIdx in range(
                        startIdx, min(startIdx + blockSize, nlabels)):

                    # A new request to re-create the list has
                    # been made - cancel this creation chain.
                    if self.__labelListCreateKey != myCreateKey:
                        return

                    label  = lut[labelIdx]
                    widget = LabelWidget(self, lut, label)

                    self.__labelList.Append(str(label.value),
                                            clientData=label.value,
                                            extraWidget=widget)

                if labelIdx == nlabels - 1:
                    status.update('Lookup table label list created.')
                    self.Enable()
                    self.__labelList.Enable()
                else:
                    async.idle(addLabel, labelIdx + 1)

            except wx.PyDeadObjectError:
                pass

        log   .debug( 'Creating lookup table label list')
        status.update('Creating lookup table label list...', timeout=None)

        self.__labelList.Disable()
        self.Disable()
        async.idle(addLabel, 0)


    def __setLut(self, lut):
        """Updates this ``LookupTablePanel`` to display the labels for the
        given ``lut`` (assumed to be a :class:`.LookupTable` instance).

        If the currently selected overlay is associated with a
        :class:`.LabelOpts` instance, its :attr:`.LabelOpts.lut` property is
        set to the new ``LookupTable``.
        """

        if self.__selectedLut == lut:
            return

        log.debug('Selecting lut: {}'.format(lut))

        if self.__selectedLut is not None:
            self.__selectedLut.deregister(self._name, 'saved')
            self.__selectedLut.deregister(self._name, 'added')
            self.__selectedLut.deregister(self._name, 'removed')

        self.__selectedLut = lut

        if lut is not None:
            lut.register(self._name, self.__lutSaveStateChanged, 'saved')
            lut.register(self._name, self.__lutLabelAdded,       'added')
            lut.register(self._name, self.__lutLabelRemoved,     'removed')

        if lut is not None and self.__selectedOpts is not None:
            with props.skip(self.__selectedOpts, 'lut', self._name):
                self.__selectedOpts.lut = lut

        allLuts = fslcmaps.getLookupTables()

        self.__lutChoice.SetSelection(allLuts.index(lut))

        self.__lutSaveStateChanged()
        self.__createLabelList()


    def __lutSaveStateChanged(self, *a):
        """Called when the :attr:`.LookupTable.saved` property of the
        current :class:`LookupTable` instance changes. Sets the state
        of the *save* button accordingly.
        """
        self.__saveLutButton.Enable(not self.__selectedLut.saved)


    def __lutLabelAdded(self, lut, topic, label):
        """Called when the current :class:`.LookupTable` sends an ``'added'``
        notification, indicating that a label has been added. Updates the list
        of displayed labels.
        """
        label, idx = label
        widget     = LabelWidget(self, lut, label)
        self.__labelList.Insert(str(label.value),
                                idx,
                                clientData=label.value,
                                extraWidget=widget)


    def __lutLabelRemoved(self, lut, topic, label):
        """Called when the current :class:`.LookupTable` sends a ``'removed'``
        notification, indicating that a label has been removed. Updates the
        list of displayed labels.
        """
        label, idx = label
        self.__labelList.Delete(idx)


    def __onLutChoice(self, ev):
        """Called when the user changes the selected :class:`.LookupTable`
        via the lookup table drop down box. See the :meth:`__setLut` method..
        """

        selection = self.__lutChoice.GetSelection()
        lut       = self.__lutChoice.GetClientData(selection)

        log.debug('Lut choice: {}'.format(lut))

        self.__setLut(lut)


    def __onSelectAll(self, ev):
        """Called when the user pushes the *Select all* button. Enables
        every label on the current LUT.
        """

        for label in self.__selectedLut:
            label.enabled = True


    def __onSelectNone(self, ev):
        """Called when the user pushes the *Select none* button. Disables
        every label on the current LUT.
        """

        for label in self.__selectedLut:
            label.enabled = False


    def __onNewLut(self, ev):
        """Called when the user presses the *New LUT* button.

        Prompts the user to enter a name (via :func:`promptForLutName`), and
        then creates and registers a new :class:`.LookupTable`
        instance. Updates this ``LookupTablePanel`` via the
        :meth:`__updateLutChoices` and :meth:`__setLut` methods.
        """

        key, name = promptForLutName()

        if key is None:
            return

        log.debug('Creating and registering new '
                  'LookupTable: {}'.format(key))

        lut = fslcmaps.LookupTable(key=key, name=name)
        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        self.__updateLutChoices()
        self.__setLut(lut)


    def __onCopyLut(self, ev):
        """Called when the user presses the *Copy LUT* button.

        Prompts the user to enter a name (via :func:`promptForLutName`), and
        then creates and registers a new :class:`.LookupTable` instance which
        is initialised with the same labels as the previously selected
        ``LookupTable``. Updates this ``LookupTablePanel`` via the
        :meth:`__updateLutChoices` and :meth:`__setLut` methods.
        """

        oldKey  = self.__selectedLut.key
        oldName = self.__selectedLut.name

        newKey, newName = promptForLutName('{} copy'.format(oldName))

        if newKey is None:
            return

        log.debug('Creating and registering new '
                  'LookupTable {} (copied from {})'.format(newKey, oldKey))

        lut = fslcmaps.LookupTable(key=newKey, name=newName)

        for label in self.__selectedLut.labels():
            lut.insert(label.value,
                       name=label.name,
                       colour=label.colour,
                       enabled=label.enabled)

        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        self.__updateLutChoices()
        self.__setLut(lut)


    def __onLoadLut(self, ev):
        """Called when the user presses the *Load LUT* button.  Does the
        following:

          - Prompts the user to select a LUT file with a ``wx.FileDialog``

          - Prompts the user to enter a name for the LUT via the
            :func:`promptForLutName` function.

          - Creates and registers a new :class:`.LookupTable` instance,
            initialising it with the selected file.

          - Updates this ``LookupTablePanel`` via the
            :meth:`__updateLutChoices` and :meth:`__setLut` methods.
        """

        parent  = wx.GetApp().GetTopWindow()
        loadDir = fslsettings.read('fsleyes.loadlutdir', os.getcwd())

        # Prompt the user to select a lut file
        fileDlg = wx.FileDialog(
            parent,
            defaultDir=loadDir,
            message=strings.titles[self, 'loadLut'],
            style=wx.FD_OPEN)

        if fileDlg.ShowModal() != wx.ID_OK:
            return

        lutFile = fileDlg.GetPath()
        lutDir  = op.dirname(lutFile)
        lutName = op.splitext(op.basename(lutFile))[0]

        # Prompt the user to enter a name
        lutKey, lutName = promptForLutName(lutName)
        if lutKey is None:
            return

        # Register the lut
        lut = fslcmaps.registerLookupTable(lutFile,
                                           self._overlayList,
                                           self._displayCtx,
                                           key=lutKey,
                                           name=lutName)

        # Save the directory for next time
        fslsettings.write('fsleyes.loadlutdir', lutDir)

        # Select the lut in the panel
        self.__updateLutChoices()
        self.__setLut(lut)


    def __onSaveLut(self, ev):
        """Called when the user presses the *Save LUT* button. Makes sure
        that the current :class:`LookupTable` is saved (see the
        :func:`.colourmaps.installLookupTable` function).
        """
        etitle = strings.titles[  self, 'installerror']
        emsg   = strings.messages[self, 'installerror']
        with status.reportIfError(title=etitle, msg=emsg, raiseError=False):
            fslcmaps.installLookupTable(self.__selectedLut.key)


    def __onLabelAdd(self, ev):
        """Called when the user pushes the *add* button on the lookup table
        label list. Displays a :class:`LutLabelDialog`, prompting the user
        to select a name, value and colour, and then adds a new label to the
        current :class:`.LookupTable` instance.
        """

        lut    = self.__selectedLut
        value  = lut.max() + 1
        name   = strings.labels['LutLabelDialog.newLabel']
        colour = fslcmaps.randomBrightColour()
        colour = [int(round(c * 255.0)) for c in colour]

        dlg = LutLabelDialog(self.GetTopLevelParent(), value, name, colour)
        if dlg.ShowModal() != wx.ID_OK:
            return

        lut    = self.__selectedLut
        value  = dlg.GetValue()
        name   = dlg.GetName()
        colour = dlg.GetColour()[:3]
        colour = [c / 255.0 for c in colour]

        if lut.get(value) is not None:
            wx.MessageBox(
                strings.messages[self, 'labelExists'].format(lut.name, value),
                strings.titles[  self, 'labelExists'], (wx.ICON_INFORMATION |
                                                        wx.OK))
            return

        log.debug('New lut label for {}: {}, {}, {}'.format(
            lut.name,
            value,
            name,
            colour))

        with lut.skip(self._name, 'added'):
            label  = lut.insert(value, name=name, colour=colour)
            widget = LabelWidget(self, lut, label)
            idx    = lut.index(label)
            self.__labelList.Insert(str(label.value),
                                    idx,
                                    clientData=label.value,
                                    extraWidget=widget)


    def __onLabelRemove(self, ev):
        """Called when the user pushes the *remove* button on the lookup
        table label list. Removes the selected label from the current
        :class:`.LookupTable`.
        """

        idx   = self.__labelList.GetSelection()
        lut   = self.__selectedLut
        value = lut[idx].value

        with lut.skip(self._name, 'removed'):
            lut.delete(value)
        self.__labelList.Delete(idx)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes.  Refreshes the
        ``LookupTablePanel`` accordingly.
        """

        newOverlay = self._displayCtx.getSelectedOverlay()

        if self.__selectedOverlay is not None and \
           self.__selectedOverlay in self._overlayList:

            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('overlayType', self._name)

        self.__selectedOverlay = newOverlay

        if newOverlay is not None:

            display = self._displayCtx.getDisplay(newOverlay)
            display.addListener('overlayType',
                                self._name,
                                self.__overlayTypeChanged)

        self.__overlayTypeChanged()


    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` property of the
        currently selected overlay changes. If the :class:`.DisplayOpts`
        instance associated with the new overlay type is a
        :class:`.LabelOpts`, a listener is addd to its ``lut`` property.
        """

        if self.__selectedOpts is not None:
            self.__selectedOpts.removeListener('lut', self._name)
            self.__selectedOpts = None

        overlay = self.__selectedOverlay
        opts    = None

        if overlay is None:
            return

        opts = self._displayCtx.getOpts(overlay)

        if not isinstance(opts, (displayctx.LabelOpts, displayctx.MeshOpts)):

            # If the image is a Melodic image, show
            # the melodic classification lut
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.__setLut(fslcmaps.getLookupTable('melodic-classes'))

            return

        opts.addListener('lut', self._name, self.__lutChanged)

        self.__selectedOpts = opts
        self.__lutChanged()
        self.Layout()


    def __lutChanged(self, *a):
        """Called when the :attr:`.LabelOpts.lut` property associated
        with the currently selected overlay changes. Changes the
        :class:`.LookupTable` displayed  on this ``LookupTablePanel`` (see
        the  :meth:`__setLut` method).
        """
        self.__setLut(self.__selectedOpts.lut)


def promptForLutName(initial=None):
    """Prompts the user to enter a name for a newly created
    :class:`.LookupTable`.
    """

    if initial is None:
        initial = strings.labels[LookupTablePanel, 'newLutDefault']

    nameMsg   = strings.messages[LookupTablePanel, 'newlut']
    nameTitle = strings.titles[  LookupTablePanel, 'newlut']

    while True:
        dlg = wx.TextEntryDialog(
            wx.GetApp().GetTopWindow(),
            nameMsg,
            nameTitle,
            initial)

        if dlg.ShowModal() != wx.ID_OK:
            return None, None

        lutName = dlg.GetValue()
        lutKey  = fslcmaps.makeValidMapKey(lutName)

        # a lut with the specified name already exists
        if fslcmaps.isLookupTableRegistered(lutKey):
            nameMsg = strings.messages[LookupTablePanel, 'alreadyinstalled']
            continue

        break

    return lutKey, lutName


class LabelWidget(wx.Panel):
    """A ``LabelWidget`` is shown for each label of the :class:`.LookupTable`
    which is currently displayed on a :class:`LookupTablePanel`. A
    ``LabelWidget`` allows the user to change the colour and visibility of the
    label value.
    """


    def __init__(self, lutPanel, lut, label):
        """Create a ``LabelWidget``.

        :arg lutPanel: The :class:`LookupTablePanel` that is displaying this
                       ``LabelWidget``.

        :arg lut:      The :class:`.LookupTable` currently being displayed.

        :arg label:    The :class:`.LutLabel` that this ``LabelWidget`` is
                       associated with.
        """
        wx.Panel.__init__(self, lutPanel)

        self.__lutPanel = lutPanel
        self.__lut      = lut
        self.__label    = label

        self.__name   = props.makeWidget(self, label, 'name')
        self.__enable = props.makeWidget(self, label, 'enabled')
        self.__colour = props.makeWidget(self, label, 'colour')

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__enable)
        self.__sizer.Add(self.__colour)
        self.__sizer.Add(self.__name, flag=wx.EXPAND)


class LutLabelDialog(wx.Dialog):
    """A dialog which is displayed when the user adds a new label to the
    :class:`.LookupTable` currently displayed in the
    :class:`LookupTablePanel`.

    Prompts the user to enter a label value, name, and colour. After the
    dialog is dismissed, the entered information is available via the
    following methods:

    .. autosummary::
       :nosignatures:

       GetValue
       GetName
       GetColour
    """


    def __init__(self, parent, value, name, colour):
        """Create a ``LutLabelDialog``.

        :arg parent: The :mod:`wx` parent object.
        """

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self.__value  = wx.SpinCtrl(        self, min=0, max=65535)
        self.__name   = wx.TextCtrl(        self)
        self.__colour = wx.ColourPickerCtrl(self)

        self.__valueLabel  = wx.StaticText(self)
        self.__nameLabel   = wx.StaticText(self)
        self.__colourLabel = wx.StaticText(self)

        self.__ok     = wx.Button(self, id=wx.ID_OK)
        self.__cancel = wx.Button(self, id=wx.ID_CANCEL)

        self.__valueLabel .SetLabel(strings.labels[self, 'value'])
        self.__nameLabel  .SetLabel(strings.labels[self, 'name'])
        self.__colourLabel.SetLabel(strings.labels[self, 'colour'])
        self.__ok         .SetLabel(strings.labels[self, 'ok'])
        self.__cancel     .SetLabel(strings.labels[self, 'cancel'])

        self.__value      .SetValue( value)
        self.__name       .SetValue( name)
        self.__colour     .SetColour(colour)

        self.__sizer = wx.GridSizer(4, 2, 0, 0)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__valueLabel,
                         flag=wx.EXPAND | wx.TOP | wx.LEFT,
                         border=15)
        self.__sizer.Add(self.__value,
                         flag=wx.EXPAND | wx.TOP | wx.RIGHT,
                         border=15)
        self.__sizer.Add(self.__nameLabel,
                         flag=wx.EXPAND | wx.LEFT,
                         border=15)
        self.__sizer.Add(self.__name,
                         flag=wx.EXPAND | wx.RIGHT,
                         border=15)
        self.__sizer.Add(self.__colourLabel,
                         flag=wx.EXPAND | wx.LEFT,
                         border=15)
        self.__sizer.Add(self.__colour,
                         flag=wx.EXPAND | wx.RIGHT,
                         border=15)
        self.__sizer.Add(self.__ok,
                         flag=wx.EXPAND | wx.BOTTOM | wx.LEFT,
                         border=15)
        self.__sizer.Add(self.__cancel,
                         flag=wx.EXPAND | wx.BOTTOM | wx.RIGHT,
                         border=15)

        self.__ok    .Bind(wx.EVT_BUTTON, self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        self.__ok.SetDefault()

        self.Layout()
        self.Fit()

        self.CentreOnParent()

        self.__enteredValue  = None
        self.__enteredName   = None
        self.__enteredColour = None


    def GetValue(self):
        """Returns the value that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """
        return self.__enteredValue


    def GetName(self):
        """Returns the name that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """
        return self.__enteredName


    def GetColour(self):
        """Returns the colour that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """
        return self.__enteredColour


    def __onOk(self, ev):
        """Called when the user confirms the dialog. Saves the name, colour,
        and value that were entered, and closes the dialog.
        """
        self.__enteredValue  = self.__value .GetValue()
        self.__enteredName   = self.__name  .GetValue()
        self.__enteredColour = self.__colour.GetColour()

        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the user cancells the dialog. Closes the dialog."""

        self.EndModal(wx.ID_CANCEL)
