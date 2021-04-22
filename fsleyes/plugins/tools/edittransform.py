#!/usr/bin/env python
#
# edittransform.py - The EditTransformPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`EditTransformPanel` (a.k.a. "Nudge")
class, a FSLeyes control panel which allows the user to adjust the
``voxToWorldMat`` of an :class:`.Image` overlay.
"""


import logging

import wx

import numpy as np

import fsl.data.image                       as fslimage
import fsl.utils.idle                       as idle
import fsl.transform.affine                 as affine

import fsleyes_props                        as props
import fsleyes_widgets.floatslider          as fslider

import fsleyes.actions                      as actions
import fsleyes.views.orthopanel             as orthopanel
import fsleyes.controls.controlpanel        as ctrlpanel
import fsleyes.displaycontext               as displaycontext
import fsleyes.strings                      as strings
import fsleyes.plugins.tools.applyflirtxfm  as applyflirtxfm
import fsleyes.plugins.tools.saveflirtxfm   as saveflirtxfm
import fsleyes.controls.displayspacewarning as dswarning


log = logging.getLogger(__name__)


class EditTransformAction(actions.ToggleControlPanelAction):
    """The ``EditTransformAction`` just toggles an
    :class:`.EditTransformPanel`. It is added under the FSLeyes Tools menu.
    """

    @staticmethod
    def supportedViews():
        """The ``EditTransformAction`` is restricted for use with
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    def __init__(self, overlayList, displayCtx, ortho):
        """Create an ``EditTransformAction``.
        """
        super().__init__(overlayList, displayCtx, ortho, EditTransformPanel)
        self.__ortho = ortho

        displayCtx.addListener('selectedOverlay', self.name,
                               self.__selectedOverlayChanged)


    def destroy(self):
        """Called when the :class:`.OrthoPanel` that owns this action is
        closed. Clears references, removes listeners, and calls the base
        class ``destroy`` method.
        """
        if self.destroyed:
            return

        self.__ortho = None
        self.displayCtx.removeListener('selectedOverlay', self.name)
        super().destroy()


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay changes. Enables/disables this
        action (and hence the bound Tools menu item) depending on whether the
        overlay is an image.
        """
        ovl = self.displayCtx.getSelectedOverlay()
        self.enabled = isinstance(ovl, fslimage.Image)


class EditTransformPanel(ctrlpanel.ControlPanel):
    """The :class:`EditTransformPanel` class is a FSLeyes control panel which
    allows the user to adjust the ``voxToWorldMat`` of an :class:`.Image`
    overlay.


    Controls are provided allowing the user to construct a transformation
    matrix from scales, offsets, and rotations. While the user is adjusting
    the transformation, the :attr:`.NiftiOpts.displayXform` is used to
    update the overlay display in real time. When the user clicks the *Apply*
    button, the transformation is applied to the image's ``voxToWorldMat``
    attribute.


    This panel also has buttons which allow the user to load/save the
    transformation matrix - they use functions in the :mod:`.applyflirtxfm`
    and :mod:`.saveflirtxfm` modules to load, save, and calculate
    transformation matrices. When the user loads a matrix, it is used in place
    of the :attr:`.Image.voxToWorldMat` transformation.

    .. note:: The effect of editing the transformation will only be visible
              if the :attr:`.DisplayContext.displaySpace` is set to
              ``'world'``, or to some image which is not being edited. A
              warning is shown at the top of the panel if the ``displaySpace``
              is not set appropriately.
    """


    @staticmethod
    def ignoreControl():
        """Tells the FSLeyes plugin system not to add the
        ``EditTransformPanel`` as an option to the FSLeyes settings menu.
        Instead, the :class:`EditTransformAction` action is added to the
        tools menu.
        """
        return True


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``EditTransformPanel`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary of arguments to be passed to the
        :meth:`.ViewPanel.togglePanel` method when an ``EditTransformPanel``
        is created.
        """
        return dict(floatPane=True, floatOnly=True)


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``EditTransformPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """

        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, ortho)

        self.__ortho = ortho

        # A ref to the currently selected
        # (compatible) overlay is kept here.
        # The __extraXform attribute is used
        # to store a FLIRT transform if the
        # user has loaded one. This 'extra'
        # matrix is used in place of the
        # image voxToWorldMat (i.e. its sform);
        # the scale/offset/ rotate transform
        # defined by the widgets on this panel
        # is still applied.
        #
        # In the future, I might allow the
        # user to load/apply an arbitrary
        # (non-FLIRT) transform.
        self.__overlay    = None
        self.__extraXform = None

        # When the selected overlay is changed, the
        # transform settings for the previously selected
        # overlay are cached in this dict, so they can be
        # restored if/when the overlay is re-selected.
        #
        # { overlay : (scales, offsets, rotations, extraXform) }
        self.__cachedXforms = {}

        scArgs = {
            'value'    : 0,
            'minValue' : 0.001,
            'maxValue' : 3,
            'style'    : fslider.SSP_NO_LIMITS
        }

        offArgs = {
            'value'    : 0,
            'minValue' : -250,
            'maxValue' :  250,
            'style'    : fslider.SSP_NO_LIMITS
        }

        rotArgs = {
            'value'    : 0,
            'minValue' : -180,
            'maxValue' :  180,
            'style'    : 0
        }

        # rotate about the centre of the image,
        # or the current world location
        centreOpts   = ['volume', 'cursor']
        centreLabels = [strings.labels[self, 'centre.options'][o]
                        for o in centreOpts]

        self.__overlayName = wx.StaticText(self)
        self.__dsWarning   = dswarning.DisplaySpaceWarning(
            self,
            overlayList,
            displayCtx,
            self.frame,
            strings.labels[self, 'dsWarning'],
            'overlay',
            'world')

        self.__xscale  = fslider.SliderSpinPanel(self, label='X', **scArgs)
        self.__yscale  = fslider.SliderSpinPanel(self, label='Y', **scArgs)
        self.__zscale  = fslider.SliderSpinPanel(self, label='Z', **scArgs)

        self.__xoffset = fslider.SliderSpinPanel(self, label='X', **offArgs)
        self.__yoffset = fslider.SliderSpinPanel(self, label='Y', **offArgs)
        self.__zoffset = fslider.SliderSpinPanel(self, label='Z', **offArgs)

        self.__xrotate = fslider.SliderSpinPanel(self, label='X', **rotArgs)
        self.__yrotate = fslider.SliderSpinPanel(self, label='Y', **rotArgs)
        self.__zrotate = fslider.SliderSpinPanel(self, label='Z', **rotArgs)
        self.__centre  = wx.Choice(self)

        self.__scaleLabel  = wx.StaticText(self)
        self.__offsetLabel = wx.StaticText(self)
        self.__rotateLabel = wx.StaticText(self)
        self.__centreLabel = wx.StaticText(self)

        self.__oldXformLabel = wx.StaticText(self)
        self.__oldXform      = wx.StaticText(self)
        self.__newXformLabel = wx.StaticText(self)
        self.__newXform      = wx.StaticText(self)

        self.__apply     = wx.Button(self)
        self.__reset     = wx.Button(self)
        self.__loadFlirt = wx.Button(self)
        self.__saveFlirt = wx.Button(self)
        self.__cancel    = wx.Button(self)

        self.__overlayName  .SetLabel(strings.labels[self, 'noOverlay'])
        self.__scaleLabel   .SetLabel(strings.labels[self, 'scale'])
        self.__offsetLabel  .SetLabel(strings.labels[self, 'offset'])
        self.__rotateLabel  .SetLabel(strings.labels[self, 'rotate'])
        self.__centreLabel  .SetLabel(strings.labels[self, 'centre'])
        self.__apply        .SetLabel(strings.labels[self, 'apply'])
        self.__reset        .SetLabel(strings.labels[self, 'reset'])
        self.__loadFlirt    .SetLabel(strings.labels[self, 'loadFlirt'])
        self.__saveFlirt    .SetLabel(strings.labels[self, 'saveFlirt'])
        self.__cancel       .SetLabel(strings.labels[self, 'cancel'])
        self.__oldXformLabel.SetLabel(strings.labels[self, 'oldXform'])
        self.__newXformLabel.SetLabel(strings.labels[self, 'newXform'])

        self.__centre.Set(centreLabels)
        self.__centreOpts = centreOpts

        # Populate the xform labels with a
        # dummy xform, so an appropriate
        # minimum size will get calculated
        # below
        self.__formatXform(np.eye(4), self.__oldXform)
        self.__formatXform(np.eye(4), self.__newXform)

        self.__primarySizer   = wx.BoxSizer(wx.VERTICAL)
        self.__secondarySizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__controlSizer   = wx.BoxSizer(wx.VERTICAL)
        self.__xformSizer     = wx.BoxSizer(wx.VERTICAL)
        self.__buttonSizer    = wx.BoxSizer(wx.HORIZONTAL)

        self.__primarySizer  .Add((1, 10),            flag=wx.EXPAND)
        self.__primarySizer  .Add(self.__overlayName, flag=wx.CENTRE)
        self.__primarySizer  .Add(self.__dsWarning,   flag=wx.CENTRE)
        self.__primarySizer  .Add((1, 10),            flag=wx.EXPAND)
        self.__primarySizer  .Add(self.__secondarySizer)
        self.__primarySizer  .Add((1, 10),            flag=wx.EXPAND)
        self.__primarySizer  .Add(self.__buttonSizer, flag=wx.EXPAND)
        self.__primarySizer  .Add((1, 10),            flag=wx.EXPAND)

        self.__secondarySizer.Add((10, 1),           flag=wx.EXPAND)
        self.__secondarySizer.Add(self.__controlSizer)
        self.__secondarySizer.Add((10, 1),           flag=wx.EXPAND)
        self.__secondarySizer.Add(self.__xformSizer, flag=wx.EXPAND)
        self.__secondarySizer.Add((10, 1),           flag=wx.EXPAND)

        self.__controlSizer.Add(self.__scaleLabel)
        self.__controlSizer.Add(self.__xscale)
        self.__controlSizer.Add(self.__yscale)
        self.__controlSizer.Add(self.__zscale)
        self.__controlSizer.Add(self.__offsetLabel)
        self.__controlSizer.Add(self.__xoffset)
        self.__controlSizer.Add(self.__yoffset)
        self.__controlSizer.Add(self.__zoffset)
        self.__controlSizer.Add(self.__rotateLabel)
        self.__controlSizer.Add(self.__xrotate)
        self.__controlSizer.Add(self.__yrotate)
        self.__controlSizer.Add(self.__zrotate)
        self.__controlSizer.Add(self.__centreLabel)
        self.__controlSizer.Add(self.__centre)

        self.__xformSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        self.__xformSizer.Add(self.__oldXformLabel)
        self.__xformSizer.Add(self.__oldXform)
        self.__xformSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        self.__xformSizer.Add(self.__newXformLabel)
        self.__xformSizer.Add(self.__newXform)
        self.__xformSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)

        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__apply,     flag=wx.EXPAND)
        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND)
        self.__buttonSizer.Add(self.__reset,     flag=wx.EXPAND)
        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND)
        self.__buttonSizer.Add(self.__loadFlirt, flag=wx.EXPAND)
        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND)
        self.__buttonSizer.Add(self.__saveFlirt, flag=wx.EXPAND)
        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND)
        self.__buttonSizer.Add(self.__cancel,    flag=wx.EXPAND)
        self.__buttonSizer.Add((10, 1),          flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__primarySizer)
        self.SetMinSize(self.__primarySizer.GetMinSize())

        self.__xscale .Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__yscale .Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__zscale .Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__xoffset.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__yoffset.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__zoffset.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__xrotate.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__yrotate.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__zrotate.Bind(fslider.EVT_SSP_VALUE, self.__xformChanged)
        self.__centre .Bind(wx.EVT_CHOICE,         self.__xformChanged)

        self.__apply    .Bind(wx.EVT_BUTTON, self.__onApply)
        self.__reset    .Bind(wx.EVT_BUTTON, self.__onReset)
        self.__loadFlirt.Bind(wx.EVT_BUTTON, self.__onLoadFlirt)
        self.__saveFlirt.Bind(wx.EVT_BUTTON, self.__onSaveFlirt)
        self.__cancel   .Bind(wx.EVT_BUTTON, self.__onCancel)

        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``EditTransformPanel`` is no longer
        needed. Removes listeners and cleans up references.
        """

        self.__deregisterOverlay()

        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        dsWarning   = self.__dsWarning

        displayCtx .removeListener('selectedOverlay', self.name)
        overlayList.removeListener('overlays',        self.name)

        self.__ortho        = None
        self.__cachedXforms = None
        self.__dsWarning    = None

        dsWarning.destroy()
        ctrlpanel.ControlPanel.destroy(self)


    def __registerOverlay(self, overlay):
        """Called by :meth:`__selectedOverlayChanged`. Stores a reference
        to the given ``overlay``.
        """

        self.__overlay = overlay
        display = self.displayCtx.getDisplay(overlay)
        display.addListener('name', self.name, self.__overlayNameChanged)

        self.__overlayNameChanged()


    def __deregisterOverlay(self):
        """Called by :meth:`__selectedOverlayChanged`. Clears references
        to the most recently registered overlay.
        """

        if self.__overlay is None:
            return

        overlay = self.__overlay

        scales, offsets, rotations, centre = self.__getCurrentXformComponents()
        extra                              = self.__extraXform

        self.__cachedXforms[overlay] = (scales, offsets, rotations,
                                        centre, extra)

        self.__overlay    = None
        self.__extraXform = None

        self.__overlayName.SetLabel(strings.labels[self, 'noOverlay'])

        # Catch errors in case the
        # overlay has been removed
        # from the list
        try:
            display = self.displayCtx.getDisplay(overlay)
            display.removeListener('name', self.name)

        except displaycontext.InvalidOverlayError:
            pass


    def __overlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` of the currently selected
        overlay changes. Updates the name label.
        """
        display = self.displayCtx.getDisplay(self.__overlay)
        label   = strings.labels[self, 'overlayName'].format(display.name)

        self.__overlayName.SetLabel(label)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :attr:`.OverlayList.overlays` properties change. If the newly
        selected overlay is an :class:`.Image`, it is registered, and
        the transform widgets reset.
        """
        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is self.__overlay:
            return

        self.__deregisterOverlay()

        enabled = isinstance(overlay, fslimage.Image)

        self.Enable(enabled)

        if not enabled:
            return

        self.__registerOverlay(overlay)

        xform                                     = overlay.voxToWorldMat
        scales, offsets, rotations, centre, extra = self.__cachedXforms.get(
            overlay, ((1, 1, 1), (0, 0, 0), (0, 0, 0), 'volume', None))

        self.__extraXform = extra

        self.__formatXform(xform, self.__oldXform)

        # TODO Set limits based on image size?
        self.__xscale .SetValue(scales[   0])
        self.__yscale .SetValue(scales[   1])
        self.__zscale .SetValue(scales[   2])
        self.__xoffset.SetValue(offsets[  0])
        self.__yoffset.SetValue(offsets[  1])
        self.__zoffset.SetValue(offsets[  2])
        self.__xrotate.SetValue(rotations[0])
        self.__yrotate.SetValue(rotations[1])
        self.__zrotate.SetValue(rotations[2])
        self.__centre .SetSelection(self.__centreOpts.index(centre))

        self.__xformChanged()


    def __formatXform(self, xform, ctrl):
        """Format the given ``xform``  on the given ``wx.StaticText``
        ``ctrl``.
        """

        text = ''

        for rowi in range(xform.shape[0]):
            for coli in range(xform.shape[1]):

                text = text + '{: 9.2f} '.format(xform[rowi, coli])

            text = text + '\n'

        ctrl.SetLabel(text)


    def __getCurrentXformComponents(self):
        """Returns the components of the transformation matrix defined
        by the scale, offset and rotation widgets.
        """
        scales    = [self.__xscale .GetValue(),
                     self.__yscale .GetValue(),
                     self.__zscale .GetValue()]
        offsets   = [self.__xoffset.GetValue(),
                     self.__yoffset.GetValue(),
                     self.__zoffset.GetValue()]
        rotations = [self.__xrotate.GetValue(),
                     self.__yrotate.GetValue(),
                     self.__zrotate.GetValue()]
        centre    = self.__centreOpts[self.__centre.GetSelection()]

        return scales, offsets, rotations, centre


    def __getCurrentXform(self):
        """Returns the current transformation matrix defined by the scale,
        offset, and rotation widgets.
        """

        scales, offsets, rotations, centre = self.__getCurrentXformComponents()

        rotations = [r * np.pi / 180 for r in rotations]

        if centre == 'volume':
            # We need to figure out the centre
            # of the image in world coordinates
            # to define the origin of rotation.
            shape  = self.__overlay.shape
            lo, hi = affine.axisBounds(shape, self.__overlay.voxToWorldMat)
            origin = [l + (h - l) / 2.0 for h, l in zip(hi, lo)]
        else:
            origin = self.displayCtx.worldLocation

        return affine.compose(scales, offsets, rotations, origin)


    def __xformChanged(self, ev=None):
        """Called when any of the scale, offset, or rotate widgets are
        modified. Updates the :attr:`.NiftiOpts.displayXform` for the
        overlay currently being edited.
        """

        if self.__overlay is None:
            return

        overlay  = self.__overlay
        opts     = self.displayCtx.getOpts(overlay)

        if self.__extraXform is None: v2wXform = overlay.voxToWorldMat
        else:                         v2wXform = self.__extraXform

        xform = self.__getCurrentXform()
        xform = affine.concat(xform, v2wXform)

        self.__formatXform(xform, self.__newXform)

        # The NiftiOpts.displayXform is applied on
        # top of the image voxToWorldMat. But our
        # xform here has been constructed to replace
        # the voxToWorldMat entirely. So we include
        # a worldToVoxMat transform to trick the
        # NiftiOpts code.
        opts.displayXform = affine.concat(xform, overlay.worldToVoxMat)


    def __onApply(self, ev):
        """Called when the *Apply* button is pushed. Sets the
        ``voxToWorldMat`` attribute of the :class:`.Image` instance being
        transformed.
        """

        overlay = self.__overlay

        if overlay is None:
            return

        if self.__extraXform is None: v2wXform = overlay.voxToWorldMat
        else:                         v2wXform = self.__extraXform

        newXform = self.__getCurrentXform()
        opts     = self.displayCtx.getOpts(overlay)

        xform = affine.concat(newXform, v2wXform)

        with props.suppress(opts, 'displayXform'):
            opts.displayXform     = np.eye(4)
            overlay.voxToWorldMat = xform

        # Reset the interface, and clear any
        # cached transform for this overlay
        self.__deregisterOverlay()
        self.__cachedXforms.pop(overlay, None)
        self.__selectedOverlayChanged()


    def __resetAllOverlays(self):
        """Resets the :attr:`.NiftiOpts.displayXform` matrix for
        all overlays that have been modified, and clears the internal
        transformation matrix cache.

        This method is called by :meth:`__onReset` and :meth:`__onCancel`.
        """

        reset = list(self.__cachedXforms.keys())

        if self.__overlay is not None:
            reset.append(self.__overlay)

        self.__deregisterOverlay()
        self.__cachedXforms = {}

        for overlay in reset:
            try:
                opts = self.displayCtx.getOpts(overlay)
                opts.displayXform = np.eye(4)

            # In cas overlay has been removed
            except displaycontext.InvalidOverlayError:
                pass


    def __onReset(self, ev=None):
        """Called when the *Reset* button is pushed. Resets the
        transformation.
        """

        self.__resetAllOverlays()
        self.__selectedOverlayChanged()


    def __onLoadFlirt(self, ev):
        """Called when the user clicks the *Load FLIRT transform* button.
        Prompts the user to choose a FLIRT transformation matrix and reference
        image, and then applies the transformation.
        """

        overlay = self.__overlay

        if overlay is None:
            return

        overlayList               = self.overlayList
        displayCtx                = self.displayCtx
        affType, matFile, refFile = applyflirtxfm.promptForFlirtFiles(
            self,
            overlay,
            overlayList,
            displayCtx)

        if all((affType is None, matFile is None, refFile is None)):
            return

        if affType == 'flirt':
            xform = applyflirtxfm.calculateTransform(
                overlay,
                overlayList,
                displayCtx,
                matFile,
                refFile)

        elif affType == 'v2w':
            xform = np.loadtxt(matFile)

        self.__extraXform = xform
        self.__xformChanged()


    def __onSaveFlirt(self, ev):
        """Called when the user clicks the *Save FLIRT* button. Saves the
        current transformation to a FLIRT matrix file.
        """

        overlay = self.__overlay

        if overlay is None:
            return

        overlayList               = self.overlayList
        displayCtx                = self.displayCtx
        affType, matFile, refFile = applyflirtxfm.promptForFlirtFiles(
            self,
            overlay,
            overlayList,
            displayCtx,
            save=True)

        if all((affType is None, matFile is None, refFile is None)):
            return

        if self.__extraXform is None: v2wXform = overlay.voxToWorldMat
        else:                         v2wXform = self.__extraXform

        newXform = self.__getCurrentXform()
        v2wXform = affine.concat(newXform, v2wXform)

        if affType == 'flirt':
            xform = saveflirtxfm.calculateTransform(
                overlay,
                overlayList,
                displayCtx,
                refFile,
                srcXform=v2wXform)
        elif affType == 'v2w':
            xform = v2wXform

        try:
            np.savetxt(matFile, xform, fmt='%0.10f')

        except Exception as e:

            log.warning('Error saving FLIRT matrix: %s', e)

            wx.MessageDialog(
                self,
                strings.messages[self, 'saveFlirt.error'].format(str(e)),
                style=wx.ICON_ERROR).ShowModal()


    def __onCancel(self, ev=None):
        """Called when the *Cancel* button is pushed. Resets the
        :attr:`.NiftiOpts.displayXform` attribute of the overlay being
        transformed, and then calls
        :meth:`.OrthoPanel.toggleEditTransformPanel` to close this panel.
        """

        self.__resetAllOverlays()
        idle.idle(self.__ortho.togglePanel, type(self))
