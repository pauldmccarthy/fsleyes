#!/usr/bin/env python
#
# strings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a collection of strings used throughout ``fslpy`` for
display purposes. Most of the strings are used by FSLeyes.


The strings are stored in :class:`.TypeDict` dictionaries, roughly organised
into the following categories:


 ==================== =====================================================
 :data:`messages`     Messages to be displayed to the user.
 :data:`titles`       Titles of windows, panels, and dialogs.
 :data:`actions`      Names of actions tied to menu options, buttons, etc.
 :data:`labels`       Labels for miscellaneous things.
 :data:`properties`   Display names for ``props.HasProperties`` properties.
 :data:`choices`      Display names for ``props.HasProperties`` choice
                      properties.
 :data:`anatomy`      Anatomical and orientation labels.
 :data:`nifti`        Labels for NIFTI header fields.
 :data:`feat`         FEAT specific names and labels.
 :data:`melodic`      MELODIC specific names and labels.
 :data:`perspectives` Perspective labels.
 :data:`tensor`       Tensor overlay labels.
 :data:`plotLabels`   Labels to use for plot data loaded from known files.
 :data:`about`        Strings used in the *FSLeyes* about dialog.
 ==================== =====================================================
"""


import textwrap

from   fsleyes_widgets.utils.typedict import TypeDict
import fsl.data.constants                 as constants


messages = TypeDict({

    'FSLeyesSplash.default' : 'Loading ...',

    'FSLeyesFrame.restoringLayout'     : 'Restoring layout from last '
                                         'session ...',
    'FSLeyesFrame.saveLayout'          : 'Save this layout for next time?',
    'FSLeyesFrame.dontAskToSaveLayout' : 'Never ask me again',
    'FSLeyesFrame.unsavedOverlays'     : 'You have unsaved images - are '
                                         'you sure you want to exit?',

    'perspectives.applyingPerspective' : 'Applying {} perspective ...',

    'SavePerspectiveAction.enterName'        : 'Enter a name for the '
                                               'perspective',
    'SavePerspectiveAction.nameIsBuiltIn'    : '"{}" is a reserved '
                                               'perspective name - '
                                               'enter a different name.',
    'SavePerspectiveAction.confirmOverwrite' : 'A perspective with the name '
                                               '"{}" already exists - do '
                                               'you want to replace it?',

    'ClearPerspectiveAction.confirmClear' : 'All saved perspectives will be '
                                            'cleared! Are you sure you want '
                                            'to continue?',

    'FSLeyesApp.openURLError' : 'An error occurred loading the URL.',

    'SliceCanvas.globjectError'  :
    'An error occurred initialising the display for {}',

    'Texture3D.dataError'  :
    'An error occurred updating the texture data',

    'SaveOverlayAction.overwrite'      : 'Do you want to overwrite {}, or '
                                         'save the image to a new file?',

    'loadOverlays.loading'     : 'Loading {} ...',
    'loadOverlays.error'       : 'An error occurred loading the image {}',

    'loadOverlays.unknownType' : 'Unknown data type',

    'LoadColourMapAction.loadcmap'    : 'Open colour map file',
    'LoadColourMapAction.namecmap'    : 'Enter a name for the colour map.',

    'LoadColourMapAction.installcmap' :
    'Do you want to install this colour map permanently?',

    'LoadColourMapAction.alreadyinstalled' :
    'A colour map with that name already exists - choose a different name.',

    'LoadColourMapAction.installerror'     :
    'An error occurred while installing the colour map. ',

    'LookupTablePanel.newlut' :
    'Enter a name for the lookup table.',
    'LookupTablePanel.alreadyinstalled' :
    'A lookup table with that name already exists - choose a different name.',
    'LookupTablePanel.installerror' :
    'An error occurred while installing the lookup table.',

    'actions.copyoverlay.createMask'  : 'Create empty mask image '
                                        'with same dimensions',
    'actions.copyoverlay.copyDisplay' : 'Copy display properties',
    'actions.copyoverlay.copy4D'      : 'Copy 4D image',

    'RunScriptAction.runScript' : 'Choose a FSLeyes script to run',
    'RunScriptAction.crash'     : 'The script {} has crashed! Reason: {}',

    'AtlasPanel.loadingAtlas' : 'Loading {} atlas ...',

    'AtlasOverlayPanel.loadRegions'    : 'Loading region descriptions '
                                         'for {} ...',
    'AtlasOverlayPanel.regionsLoaded'  : '{} region descriptions loaded.',

    'AtlasOverlayPanel.loadAtlasError' : 'An error occurred while trying '
                                        'to load the atlas overlay for '
                                        '"{}":\nDetails: {}',

    'AtlasInfoPanel.notMNISpace'   : 'The selected overlay does not appear to '
                                     'be in MNI152 space - atlas '
                                     'information might not be accurate!' ,

    'AtlasInfoPanel.chooseAnAtlas' : 'Choose an atlas!',
    'AtlasInfoPanel.atlasDisabled' : 'Atlases are not available',

    'AtlasInfoPanel.loadAtlasError' : 'An error occurred while trying '
                                      'to load the atlas "{}":\nDetails: {}',

    'CanvasPanel.screenshot'            : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved'   : 'Overlay {} needs saving before a '
                                          'screenshot can be taken.',
    'CanvasPanel.screenshot.pleaseWait' : 'Saving screenshot to {}...',
    'CanvasPanel.screenshot.error'      : 'An error occurred saving the '
                                          'screenshot.',

    'CanvasPanel.showCommandLineArgs.title'   : 'Scene parameters',
    'CanvasPanel.showCommandLineArgs.message' : 'Use these parameters on the '
                                                'command line to recreate '
                                                'the current scene',

    'PlotPanel.screenshot'              : 'Save screenshot',

    'PlotPanel.screenshot.error'       : 'An error occurred while saving the '
                                         'screenshot.\n\n'
                                         'Details: {}',

    'PlotPanel.preparingData'          : 'Preparing data - please wait...',

    'HistogramPanel.calcHist'           : 'Calculating histogram for {} ...',

    'LookupTablePanel.labelExists' : 'The {} LUT already contains a '
                                     'label with value {}',

    'ClusterPanel.noOverlays'     : 'Add a FEAT overlay',
    'ClusterPanel.notFEAT'        : 'Choose a FEAT overlay',
    'ClusterPanel.noClusters'     : 'No cluster results exist '
                                    'in this FEAT analysis',
    'ClusterPanel.badData'        : 'Cluster data could not be parsed - '
                                    'check your cluster_*.txt files.',
    'ClusterPanel.loadingCluster' : 'Loading clusters for COPE{} ({}) ...',

    'OrthoPanel.toggleEditTransformPanel.displaySpaceChange' :
    'You are now transforming {}. ',

    'OrthoPanel.toggleEditTransformPanel.displaySpaceChange.hint' :
    'Setting the display space to world coordinates - \n'
    'this is required when transforming images.',

    'OrthoPanel.toggleEditTransformPanel.displaySpaceChange.suppress' :
    'Do not show this message again',

    'OrthoEditProfile.imageChange'        : 'You are now editing {}. ',
    'OrthoEditProfile.imageChangeHint'    : 'Setting {} as the display '
                                            'space reference\nimage - the '
                                            'display space must match the '
                                            'image being edited.',

    'OrthoEditProfile.imageChange.suppress' : 'Do not show this '
                                              'message again',

    'OrthoCropProfile.imageChange'        : 'You are now cropping {}. ',
    'OrthoCropProfile.imageChangeHint'    : 'Setting {} as the display '
                                            'space reference\nimage - the '
                                            'display space must match the '
                                            'image being cropped.',

    'OrthoCropProfile.imageChange.suppress' : 'Do not show this '
                                              'message again',

    'MelodicClassificationPanel.disabled' :
    'Choose a melodic or other 4D image.',
    'MelodicClassificationPanel.loadError' :
    'An error occurred while loading the file {}.',
    'MelodicClassificationPanel.noMelDir' :
    'The label file {} does not specify a path to a Melodic directory!',
    'MelodicClassificationPanel.saveError' :
    'An error occurred while saving the file {}.',
    'MelodicClassificationPanel.wrongNComps' :
    'The mumber of components in the label file {} is greater than the number '
    'of components in the overlay {}!',
    'MelodicClassificationPanel.diffMelDir' :
    'The label file {} does not refer to the melodic directory of the '
    'selected overlay ({}). What do you want to do?',
    'MelodicClassificationPanel.diffMelDir.labels'  :
    'Load the overlay in the label file',
    'MelodicClassificationPanel.diffMelDir.overlay' :
    'Apply the labels to the current overlay',

    'SaveOverlayAction.saveError' :
    'An error occurred while saving the file {}.',

    'removeoverlay.unsaved' :
    'This image has unsaved changes - are you sure you want to remove it?',

    'reloadoverlay.unsaved' :
    'This image has unsaved changes - are you sure you want to reload it?',

    'RemoveAllOverlaysAction.unsavedOverlays' :
    'You have unsaved images - are you sure you want to remove them all?',

    'ImportDataSeriesAction.selectFile'   :
    'Import data series from',

    'ImportDataSeriesAction.error'        :
    'Could not load {}! Details:\n\n{}',

    'ImportDataSeriesAction.selectXScale' :
    'Set the X axis sampling rate/scaling factor',

    'ExportDataSeriesAction.selectFile'   : 'Export data series to',
    'ExportDataSeriesAction.saveXColumn'  : 'Export the X axis data '
                                            'as the first column?',

    'LoadAtlasAction.error'       :
    'An error occurred loading the atlas specification {}.',

    'ClearSettingsAction.confirm' :
    'Are you sure you want to clear all FSLeyes settings? All preferences, '
    'saved perspectives, colour maps, lookup tables, and loaded atlases will '
    'be lost!\n\nYou will need to restart FSLeyes for some changes to take '
    'effect.',

    'CorrelateAction.calculating' :
    'Calculating correlation values for seed voxel [{}, {}, {}] ...',

    'EditTransformPanel.saveFlirt.error' :
    'An error occurred saving the FLIRT matrix.',

    'SaveFlirtXfmAction.error' :
    'An error occurred saving the FLIRT matrix.',

    'FlirtFileDialog.matFile'    : 'Select FLIRT transformation matrix file',
    'FlirtFileDialog.refFile'    : 'Select FLIRT reference image',


    'LoadVertexDataAction.loadVertexData' :
    'Select a vertex data file for {}',
    'LoadVertexDataAction.error' :
    'An error occurred while loading the vertex data for {}',

    'UpdateCheckAction.newVersionAvailable' :
    'A new version of FSLeyes is available. This version of FSLeyes is {}, '
    'and the latest is {}.\n\nVisit {} to upgrade!',

    'UpdateCheckAction.upToDate' :
    'Your version of FSLeyes ({}) is up to date.',

    'UpdateCheckAction.newVersionError' :
    'An error occurred while checking for FSLeyes updates. Try again later.',

    'ApplyCommandLineAction.apply' :
    'Type/paste FSLeyes command line arguments into the field below.',

    'ApplyCommandLineAction.error' :
    'An error occurred while applying the command line arguments.',
})


titles = TypeDict({

    'interactiveLoadOverlays.fileDialog' : 'Open overlay files',
    'interactiveLoadOverlays.dirDialog'  : 'Open overlay directories',

    'loadOverlays.error'  : 'Error loading overlay',

    'FSLeyesFrame.saveLayout'      : 'Save layout',
    'FSLeyesFrame.unsavedOverlays' : 'Unsaved images',

    'FSLeyesApp.openURLError' : 'Error loading URL',

    'OrthoPanel'         : 'Ortho View',
    'LightBoxPanel'      : 'Lightbox View',
    'TimeSeriesPanel'    : 'Time series',
    'PowerSpectrumPanel' : 'Power spectra',
    'HistogramPanel'     : 'Histogram',
    'ShellPanel'         : 'Python shell',

    'SliceCanvas.globjectError'  : 'Error initialising display',
    'Texture3D.dataError'        : 'Error updating data',

    'CanvasPanel.screenshot'          : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved' : 'Save overlay before continuing',
    'CanvasPanel.screenshot.error'    : 'Error saving screenshot',

    'PlotPanel.screenshot.error'      : 'Error saving screenshot',

    'AtlasInfoPanel'       : 'Atlas information',
    'AtlasOverlayPanel'    : 'Atlas search',
    'AtlasManagementPanel' : 'Atlas management',

    'OverlayListPanel'          : 'Overlay list',
    'AtlasPanel'                : 'Atlases',
    'LocationPanel'             : 'Location',
    'OverlayDisplayToolBar'     : 'Display toolbar',
    'CanvasSettingsPanel'       : 'View settings',
    'OverlayDisplayPanel'       : 'Display settings',
    'OrthoToolBar'              : 'Ortho view toolbar',
    'OrthoEditToolBar'          : 'Ortho view edit toolbar',
    'OrthoEditActionToolBar'    : 'Ortho view edit action toolbar',
    'OrthoEditSettingsPanel'    : 'Ortho view edit settings',
    'LightBoxToolBar'           : 'Lightbox view toolbar',
    'LookupTablePanel'          : 'Lookup tables',
    'LutLabelDialog'            : 'New LUT label',

    'PlotListPanel'             : 'Plot list',
    'TimeSeriesControlPanel'    : 'Time series control',
    'HistogramControlPanel'     : 'Histogram control',
    'PowerSpectrumControlPanel' : 'Power spectrum control',
    'ClusterPanel'              : 'Cluster browser',
    'OverlayInfoPanel'          : 'Overlay information',
    'PlotToolBar'               : 'Plot toolbar',
    'TimeSeriesToolBar'         : 'Time series toolbar',
    'HistogramToolBar'          : 'Histogram toolbar',

    'MelodicClassificationPanel' : 'Melodic IC classification',

    'CropImagePanel'             : 'Crop',
    'EditTransformPanel'         : 'Nudge',

    'LookupTablePanel.newlut'       : 'Name lookup table',
    'LookupTablePanel.loadLut'      : 'Select a lookup table file',
    'LookupTablePanel.labelExists'  : 'Label already exists',
    'LookupTablePanel.installerror' : 'Error installing lookup table',

    'MelodicClassificationPanel.loadDialog' : 'Load FIX/Melview file...',
    'MelodicClassificationPanel.saveDialog' : 'Save FIX/Melview file...',
    'MelodicClassificationPanel.loadError'  : 'Error loading FIX/Melview file',
    'MelodicClassificationPanel.saveError'  : 'Error saving FIX/Melview file',

    'ClearPerspectiveAction.confirmClear'  : 'Clear all perspectives?',
    'DiagnosticReportAction.saveReport'    : 'Save diagnostic report',
    'SaveOverlayAction.overwrite'          : 'Overwrite existing file?',
    'SaveOverlayAction.saveFile'           : 'Save overlay to file',
    'SaveOverlayAction.saveError'          : 'Error saving file',

    'RemoveAllOverlaysAction.unsavedOverlays' : 'Unsaved images',

    'removeoverlay.unsaved' : 'Remove unsaved image?',
    'reloadoverlay.unsaved' : 'Reload unsaved image?',

    'OrthoPanel.toolMenu'                 : 'Tools',

    'OrthoPanel.toggleEditTransformPanel.displaySpaceChange' :
    'Changing display space for transform',

    'OrthoEditProfile.imageChange'        : 'Changing edited image',
    'OrthoCropProfile.imageChange'        : 'Changing cropped image',

    'ImportDataSeriesAction.error'        : 'Error loading file',
    'ImportDataSeriesAction.selectXScale' : 'X axis scaling factor',

    'ExportDataSeriesAction.saveXColumn'  : 'Save X data?',

    'LoadAtlasAction.fileDialog'  : 'Load XML atlas specification',
    'LoadAtlasAction.error'       : 'Error loading atlas specification',

    'LoadVertexDataAction.error' : 'Error loading vertex data',

    'SaveFlirtXfmAction.error' : 'Error saving theFLIRT matrix',

    'ClearSettingsAction.confirm' : 'Clear all settings?',


    'LoadColourMapAction.namecmap'        : 'Name colour map.',
    'LoadColourMapAction.installcmap'     : 'Install colour map?',
    'LoadColourMapAction.installerror'    : 'Error installing colour map',

    'UpdateCheckAction.upToDate'            : 'FSLeyes is up to date',
    'UpdateCheckAction.newVersionAvailable' : 'New version available',
    'UpdateCheckAction.newVersionError'     : 'Error checking for updates',

    'ApplyCommandLineAction.title' : 'Apply FSLeyes command line',
    'ApplyCommandLineAction.error' : 'Error applying command line',
})


actions = TypeDict({

    'LoadOverlayAction'        : 'Add overlay from file',
    'LoadOverlayFromDirAction' : 'Add overlay from directory',
    'LoadStandardAction'       : 'Add standard',
    'CopyOverlayAction'        : 'Copy',
    'LoadAtlasAction'          : 'Add atlas',
    'ClearSettingsAction'      : 'Clear FSLeyes settings',
    'UpdateCheckAction'        : 'Check for updates',
    'SaveOverlayAction'        : 'Save',
    'ReloadOverlayAction'      : 'Reload',
    'RemoveOverlayAction'      : 'Remove',
    'RemoveAllOverlaysAction'  : 'Remove all',
    'LoadColourMapAction'      : 'Load custom colour map',
    'SavePerspectiveAction'    : 'Save current perspective',
    'ClearPerspectiveAction'   : 'Clear all perspectives',
    'DiagnosticReportAction'   : 'Diagnostic report',
    'RunScriptAction'          : 'Run script',
    'AboutAction'              : 'About FSLeyes',
    'PearsonCorrelateAction'   : 'Seed correlation (Pearson)',
    'ApplyFlirtXfmAction'      : 'Load FLIRT transformation',
    'SaveFlirtXfmAction'       : 'Export FLIRT transformation',
    'PCACorrelateAction'       : 'Seed correlation (PCA)',

    'FSLeyesFrame.removeFocusedViewPanel'  : 'Close',
    'FSLeyesFrame.addOrthoPanel'           : 'Ortho View',
    'FSLeyesFrame.addLightBoxPanel'        : 'Lightbox View',
    'FSLeyesFrame.addTimeSeriesPanel'      : 'Time series',
    'FSLeyesFrame.addHistogramPanel'       : 'Histogram',
    'FSLeyesFrame.addPowerSpectrumPanel'   : 'Power spectra',
    'FSLeyesFrame.addShellPanel'           : 'Python shell',
    'FSLeyesFrame.openHelp'                : 'Help',
    'FSLeyesFrame.closeFSLeyes'            : 'Close',
    'FSLeyesFrame.selectNextOverlay'       : 'Next',
    'FSLeyesFrame.selectPreviousOverlay'   : 'Previous',
    'FSLeyesFrame.toggleOverlayVisibility' : 'Show/hide',

    'ViewPanel.removeAllPanels'             : 'Remove all panels',

    'CanvasPanel.screenshot'                : 'Take screenshot',
    'CanvasPanel.showCommandLineArgs'       : 'Show command line for scene',
    'CanvasPanel.applyCommandLineArgs'      : 'Apply command line arguments',
    'CanvasPanel.toggleMovieMode'           : 'Movie mode',
    'CanvasPanel.toggleDisplaySync'         : 'Link display settings',
    'CanvasPanel.toggleColourBar'           : 'Colour bar',
    'CanvasPanel.toggleOverlayList'         : 'Overlay list',
    'CanvasPanel.toggleDisplayToolBar'      : 'Overlay display toolbar',
    'CanvasPanel.toggleDisplayPanel'        : 'Overlay display panel',
    'CanvasPanel.toggleCanvasSettingsPanel' : 'View settings panel',
    'CanvasPanel.toggleLocationPanel'       : 'Location panel',
    'CanvasPanel.toggleAtlasPanel'          : 'Atlas panel',
    'CanvasPanel.toggleLookupTablePanel'    : 'Lookup tables',
    'CanvasPanel.toggleClusterPanel'        : 'Cluster browser',
    'CanvasPanel.toggleOverlayInfo'         : 'Overlay information',
    'CanvasPanel.toggleClassificationPanel' : 'Melodic IC classification',

    'OrthoPanel.toggleOrthoToolBar'       : 'Ortho toolbar',
    'OrthoPanel.toggleEditMode'           : 'Edit mode',
    'OrthoPanel.toggleCropMode'           : 'Crop',
    'OrthoPanel.toggleEditTransformPanel' : 'Nudge',
    'OrthoPanel.toggleEditPanel'          : 'Edit settings panel',
    'OrthoPanel.resetDisplay'             : 'Reset display',
    'OrthoPanel.centreCursor'             : 'Centre cursor',
    'OrthoPanel.centreCursorWorld'        : 'Centre cursor at (0, 0, 0)',

    'OrthoPanel.toggleCursor'           : 'Show/hide location cursor',
    'OrthoPanel.toggleLabels'           : 'Show/hide labels',
    'OrthoPanel.toggleXCanvas'          : 'Show/hide X (sagittal) canvas',
    'OrthoPanel.toggleYCanvas'          : 'Show/hide Y (coronal) canvas',
    'OrthoPanel.toggleZCanvas'          : 'Show/hide Z (axial) canvas',

    'LightBoxPanel.toggleLightBoxToolBar' : 'Lightbox toolbar',

    'PlotPanel.screenshot'                          : 'Take screenshot',
    'PlotPanel.importDataSeries'                    : 'Import ...',
    'PlotPanel.exportDataSeries'                    : 'Export ...',
    'OverlayPlotPanel.toggleOverlayList'            : 'Overlay list',
    'TimeSeriesPanel.togglePlotList'                : 'Time series list',
    'TimeSeriesPanel.toggleTimeSeriesControl'       : 'Time series control',
    'TimeSeriesPanel.toggleTimeSeriesToolBar'       : 'Time series toolbar',
    'HistogramPanel.togglePlotList'                 : 'Histogram list',
    'HistogramPanel.toggleHistogramControl'         : 'Histogram control',
    'HistogramPanel.toggleHistogramToolBar'         : 'Histogram toolbar',
    'PowerSpectrumPanel.togglePlotList'             : 'Power spectrum list',
    'PowerSpectrumPanel.togglePowerSpectrumControl' : 'Power spectrum control',
    'PowerSpectrumPanel.togglePowerSpectrumToolBar' : 'Power spectrum toolbar',

    'OrthoViewProfile.centreCursor' : 'Centre cursor',
    'OrthoViewProfile.resetDisplay' : 'Reset display',


    'OrthoEditProfile.undo'                    : 'Undo',
    'OrthoEditProfile.redo'                    : 'Redo',
    'OrthoEditProfile.createMask'              : 'Create mask',
    'OrthoEditProfile.clearSelection'          : 'Clear selection',
    'OrthoEditProfile.fillSelection'           : 'Fill selection',
    'OrthoEditProfile.eraseSelection'          : 'Erase selection',
    'OrthoEditProfile.copySelection'           : 'Copy selection',
    'OrthoEditProfile.pasteSelection'          : 'Paste selection',
})


labels = TypeDict({

    'FSLeyesFrame.noOverlays'             : 'No overlays loaded',
    'FSLeyesFrame.noName'                 : '<unnamed>',
    'FSLeyesFrame.recentPathsMenu'        : 'Recent files',

    'LocationPanel.worldLocation'         : 'Coordinates: ',
    'LocationPanel.worldLocation.unknown' : 'Unknown',
    'LocationPanel.voxelLocation'         : 'Voxel location',
    'LocationPanel.volume'                : 'Volume',
    'LocationPanel.noData'                : 'No data',
    'LocationPanel.outOfBounds'           : 'Out of bounds',
    'LocationPanel.notAvailable'          : 'N/A',

    'OverlayListPanel.noDataSource'       : '[in memory]',

    'CanvasPanel.screenshot.notSaved.save'   : 'Save overlay now',
    'CanvasPanel.screenshot.notSaved.skip'   : 'Skip overlay (will not appear '
                                               'in screenshot)',
    'CanvasPanel.screenshot.notSaved.cancel' : 'Cancel screenshot',


    'LookupTablePanel.selectAll'   : 'Select all',
    'LookupTablePanel.selectNone'  : 'Deselect all',
    'LookupTablePanel.addLabel'    : 'Add label',
    'LookupTablePanel.removeLabel' : 'Remove label',
    'LookupTablePanel.newLut'      : 'New LUT',
    'LookupTablePanel.copyLut'     : 'Copy LUT',
    'LookupTablePanel.saveLut'     : 'Save LUT',
    'LookupTablePanel.loadLut'     : 'Load LUT',
    'LookupTablePanel.newLutDefault' : 'New LUT',

    'LutLabelDialog.value'    : 'Value',
    'LutLabelDialog.name'     : 'Name',
    'LutLabelDialog.colour'   : 'Colour',
    'LutLabelDialog.ok'       : 'Ok',
    'LutLabelDialog.cancel'   : 'Cancel',
    'LutLabelDialog.newLabel' : 'New label',


    'PlotControlPanel.plotSettings'       : 'General plot settings',
    'PlotControlPanel.customPlotSettings' : 'Custom plot settings',
    'PlotControlPanel.currentDSSettings'  : 'Plot settings for '
                                            'selected overlay ({})',
    'PlotControlPanel.customDSSettings'   : 'Custom plot settings for '
                                            'selected overlay ({})',
    'PlotControlPanel.xlim'               : 'X limits',
    'PlotControlPanel.ylim'               : 'Y limits',
    'PlotControlPanel.labels'             : 'Labels',
    'PlotControlPanel.xlabel'             : 'X',
    'PlotControlPanel.ylabel'             : 'Y',


    'TimeSeriesControlPanel.customPlotSettings' : 'Time series settings',
    'TimeSeriesControlPanel.customDSSettings'   : 'FEAT settings for '
                                                  'selected overlay ({})',

    'PowerSpectrumControlPanel.customPlotSettings' : 'Power spectrum plot '
                                                     'settings',

    'HistogramControlPanel.customPlotSettings' : 'Histogram plot settings',
    'HistogramControlPanel.customDSSettings'   : 'Histogram settings for '
                                                  'selected overlay ({})',

    'FEATModelFitTimeSeries.full' : 'Full model fit',
    'FEATModelFitTimeSeries.cope' : 'COPE{} fit: {}',
    'FEATModelFitTimeSeries.pe'   : 'PE{} fit',

    'FEATPartialFitTimeSeries.cope' : 'Reduced against COPE{}: {}',
    'FEATPartialFitTimeSeries.pe'   : 'Reduced against PE{}',

    'FEATResidualTimeSeries'     : 'Residuals',

    'ClusterPanel.clustName'     : 'Z statistics for COPE{} ({})',

    'ClusterPanel.index'         : 'Cluster index',
    'ClusterPanel.nvoxels'       : 'Size (voxels)',
    'ClusterPanel.p'             : 'P',
    'ClusterPanel.logp'          : '-log10(P)',
    'ClusterPanel.zmax'          : 'Z Max',
    'ClusterPanel.zmaxcoords'    : 'Z Max location',
    'ClusterPanel.zcogcoords'    : 'COG location',
    'ClusterPanel.copemax'       : 'COPE Max',
    'ClusterPanel.copemaxcoords' : 'COPE Max location',
    'ClusterPanel.copemean'      : 'COPE mean',

    'ClusterPanel.addZStats'    : 'Add Z statistics',
    'ClusterPanel.addClustMask' : 'Add cluster mask',


    'OverlayDisplayPanel.Display'        : 'General display settings',
    'OverlayDisplayPanel.VolumeOpts'     : 'Volume settings',
    'OverlayDisplayPanel.MaskOpts'       : 'Mask settings',
    'OverlayDisplayPanel.LabelOpts'      : 'Label settings',
    'OverlayDisplayPanel.RGBVectorOpts'  : 'RGB vector settings',
    'OverlayDisplayPanel.LineVectorOpts' : 'Line vector settings',
    'OverlayDisplayPanel.MeshOpts'       : 'Mesh settings',
    'OverlayDisplayPanel.TensorOpts'     : 'Diffusion tensor settings',
    'OverlayDisplayPanel.SHOpts'         : 'Diffusion SH settings',

    'OverlayDisplayPanel.loadCmap'       : 'Load colour map',
    'OverlayDisplayPanel.loadVertexData' : 'Load data',

    'CanvasSettingsPanel.scene'    : 'Scene settings',
    'CanvasSettingsPanel.ortho'    : 'Ortho view settings',
    'CanvasSettingsPanel.lightbox' : 'Lightbox settings',

    'OverlayInfoPanel.general'             : 'General information',
    'OverlayInfoPanel.overlayType'         : 'Displayed as',
    'OverlayInfoPanel.displaySpace'        : 'Display space',

    'OverlayInfoPanel.Nifti.dimensions'   : 'Dimensions',
    'OverlayInfoPanel.Nifti.transform'    : 'Transform/space',
    'OverlayInfoPanel.Nifti.orient'       : 'Orientation',

    'OverlayInfoPanel.Nifti.displaySpace.id'          : 'Raw voxels',
    'OverlayInfoPanel.Nifti.displaySpace.pixdim'      : 'True scaled voxels',
    'OverlayInfoPanel.Nifti.displaySpace.pixdim-flip' : 'Scaled voxels '
                                                        '(FSL convention)',
    'OverlayInfoPanel.Nifti.displaySpace.affine'      : 'World coordinates',
    'OverlayInfoPanel.Nifti.displaySpace.world'       : 'World coordinates',
    'OverlayInfoPanel.Nifti.displaySpace.custom'      : 'Scaled voxels '
                                                        '({}; FSL convention)',


    'OverlayInfoPanel.Analyze'                  : 'ANALYZE image',
    'OverlayInfoPanel.Image'                    : 'NIFTI image',
    'OverlayInfoPanel.FEATImage'                : 'NIFTI image '
                                                  '(FEAT analysis)',
    'OverlayInfoPanel.FEATImage.featInfo'       : 'FEAT information',
    'OverlayInfoPanel.MelodicImage'             : 'NIFTI image '
                                                  '(MELODIC analysis)',
    'OverlayInfoPanel.MelodicImage.melodicInfo' : 'MELODIC information',

    'OverlayInfoPanel.TriangleMesh'                        :
    'VTK model',
    'OverlayInfoPanel.TriangleMesh.numVertices'            :
    'Number of vertices',
    'OverlayInfoPanel.TriangleMesh.numTriangles'           :
    'Number of triangles',
    'OverlayInfoPanel.TriangleMesh.displaySpace'           :
    'Display space',
    'OverlayInfoPanel.TriangleMesh.refImage'               :
    'Reference image',
    'OverlayInfoPanel.TriangleMesh.coordSpace'             :
    'Vertices defined in',
    'OverlayInfoPanel.TriangleMesh.coordSpace.id'          :
    'Voxels ({})',
    'OverlayInfoPanel.TriangleMesh.coordSpace.pixdim'      :
    'Scaled voxels ({})',
    'OverlayInfoPanel.TriangleMesh.coordSpace.pixdim-flip' :
    'Scaled voxels [FSL convention] ({})',
    'OverlayInfoPanel.TriangleMesh.coordSpace.affine'      :
    'World coordinates ({})',
    'OverlayInfoPanel.TriangleMesh.coordSpace.display'     :
    'Display coordinate system',

    'OverlayInfoPanel.GiftiSurface' : 'GIFTI surface',

    'OverlayInfoPanel.dataSource'               : 'Data source',
    'OverlayInfoPanel.niftiVersion'             : 'NIFTI version',

    'OverlayInfoPanel.DTIFitTensor'             : 'DTIFit tensor images',
    'OverlayInfoPanel.DTIFitTensor.tensorInfo'  : 'Tensor image paths ',

    'MelodicClassificationPanel.componentTab'   : 'Components',
    'MelodicClassificationPanel.labelTab'       : 'Labels',
    'MelodicClassificationPanel.loadButton'     : 'Load labels',
    'MelodicClassificationPanel.saveButton'     : 'Save labels',
    'MelodicClassificationPanel.clearButton'    : 'Clear labels',

    'ComponentGrid.componentColumn'             : 'IC #',
    'ComponentGrid.labelColumn'                 : 'Labels',
    'LabelGrid.componentColumn'                 : 'IC #',
    'LabelGrid.labelColumn'                     : 'Label',

    'SaveOverlayAction.overwrite' : 'Overwrite',
    'SaveOverlayAction.saveNew'   : 'Save to new file',
    'SaveOverlayAction.cancel'    : 'Cancel',

    'ImportDataSeriesAction.firstColumnIsX' : 'First column is X data',

    'OrthoPanel.editMenu'  : 'Edit (Ortho View {})',

    'OrthoEditSettingsPanel.general' : 'General settings',
    'OrthoEditSettingsPanel.selint'  : 'Select by intensity settings',

    'CropImagePanel.cropSize3d'       :
    'Cropped shape: {:3d}, {:3d}, {:3d}',
    'CropImagePanel.cropSize4d'       :
    'Cropped shape: {:3d}, {:3d}, {:3d}, {:3d}',
    'CropImagePanel.cropSize.noImage' : 'Croppsed shape: n/a',
    'CropImagePanel.image'            : 'Crop {}',
    'CropImagePanel.image.noImage'    : 'Choose a NIFTI image',
    'CropImagePanel.cropButton'       : 'Crop',
    'CropImagePanel.robustFovButton'  : 'Robust FOV',
    'CropImagePanel.cancelButton'     : 'Cancel',

    'EditTransformPanel.noOverlay'   : 'Select a NIFTI image',
    'EditTransformPanel.overlayName' : 'Transform {}',
    'EditTransformPanel.oldXform'    : 'Original transform',
    'EditTransformPanel.newXform'    : 'New transform',
    'EditTransformPanel.scale'       : 'Scale',
    'EditTransformPanel.offset'      : 'Translate',
    'EditTransformPanel.rotate'      : 'Rotate',
    'EditTransformPanel.apply'       : 'Apply',
    'EditTransformPanel.reset'       : 'Reset',
    'EditTransformPanel.loadFlirt'   : 'Load FLIRT',
    'EditTransformPanel.saveFlirt'   : 'Save FLIRT',
    'EditTransformPanel.cancel'      : 'Close',


    'FlirtFileDialog.load.message' :
    'Select a FLIRT transformation matrix\n'
    'and the corresponding reference image.',

    'FlirtFileDialog.save.message' :
    'Specify a file name for the FLIRT transformation\n'
    'matrix, and choose the corresponding reference image.',

    'FlirtFileDialog.source'              : 'Source image:\n{}',
    'FlirtFileDialog.refChoiceSelectFile' : 'Select file manually',
    'FlirtFileDialog.matFile'             : 'Matrix file',
    'FlirtFileDialog.refFile'             : 'Reference image',
    'FlirtFileDialog.selectFile'          : 'Choose',
    'FlirtFileDialog.ok'                  : 'Ok',
    'FlirtFileDialog.cancel'              : 'Cancel',
})


properties = TypeDict({

    'DisplayContext.displaySpace'     : 'Display space',
    'DisplayContext.radioOrientation' : 'Display in radiological orientation',

    'CanvasPanel.syncLocation'       : 'Link location',
    'CanvasPanel.syncOverlayOrder'   : 'Link overlay order',
    'CanvasPanel.syncOverlayDisplay' : 'Link overlay display settings',
    'CanvasPanel.movieMode'          : 'Movie mode',
    'CanvasPanel.movieRate'          : 'Movie update rate',
    'CanvasPanel.movieAxis'          : 'Movie axis',
    'CanvasPanel.profile'            : 'Mode',

    'SceneOpts.showCursor'         : 'Show location cursor',
    'SceneOpts.cursorGap'          : 'Show gap at cursor centre',
    'SceneOpts.bgColour'           : 'Background colour',
    'SceneOpts.cursorColour'       : 'Location cursor colour',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.performance'        : 'Rendering performance',
    'SceneOpts.zoom'               : 'Zoom',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label side',

    'LightBoxOpts.zax'            : 'Z axis',
    'LightBoxOpts.highlightSlice' : 'Highlight slice',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.zrange'         : 'Z range',

    'OrthoOpts.showXCanvas' : 'Show X canvas',
    'OrthoOpts.showYCanvas' : 'Show Y canvas',
    'OrthoOpts.showZCanvas' : 'Show Z canvas',
    'OrthoOpts.showLabels'  : 'Show labels',
    'OrthoOpts.labelColour' : 'Label colour',
    'OrthoOpts.labelSize'   : 'Label size (pixels)',
    'OrthoOpts.layout'      : 'Layout',
    'OrthoOpts.xzoom'       : 'X zoom',
    'OrthoOpts.yzoom'       : 'Y zoom',
    'OrthoOpts.zzoom'       : 'Z zoom',

    'PlotPanel.legend'     : 'Show legend',
    'PlotPanel.ticks'      : 'Show ticks',
    'PlotPanel.grid'       : 'Show grid',
    'PlotPanel.gridColour' : 'Grid colour',
    'PlotPanel.bgColour'   : 'Background colour',
    'PlotPanel.smooth'     : 'Smooth',
    'PlotPanel.xAutoScale' : 'Auto-scale (x axis)',
    'PlotPanel.yAutoScale' : 'Auto-scale (y axis)',
    'PlotPanel.xLogScale'  : 'Log scale (x axis)',
    'PlotPanel.yLogScale'  : 'Log scale (y axis)',
    'PlotPanel.xlabel'     : 'X label',
    'PlotPanel.ylabel'     : 'Y label',

    'TimeSeriesPanel.plotMode'         : 'Plotting mode',
    'TimeSeriesPanel.usePixdim'        : 'Use pixdims',
    'TimeSeriesPanel.plotMelodicICs'   : 'Plot component time courses for '
                                         'Melodic images',
    'TimeSeriesPanel.plotFullModelFit' : 'Plot full model fit',
    'TimeSeriesPanel.plotResiduals'    : 'Plot residuals',

    'HistogramPanel.histType'    : 'Histogram type',

    'PowerSpectrumPanel.plotFrequencies' : 'Show frequencies along x axis ',
    'PowerSpectrumPanel.plotMelodicICs'  : 'Plot component power spectra for '
                                           'Melodic images',

    'DataSeries.colour'    : 'Colour',
    'DataSeries.alpha'     : 'Line transparency',
    'DataSeries.lineWidth' : 'Line width',
    'DataSeries.lineStyle' : 'Line style',

    'HistogramSeries.nbins'           : 'Number of bins',
    'HistogramSeries.autoBin'         : 'Automatic histogram binning',
    'HistogramSeries.ignoreZeros'     : 'Ignore zeros',
    'HistogramSeries.includeOutliers' : 'Include values out of data range',
    'HistogramSeries.volume'          : 'Volume',
    'HistogramSeries.dataRange'       : 'Data range',
    'HistogramSeries.showOverlay'     : 'Show 3D histogram overlay',

    'PowerSpectrumSeries.varNorm'     : 'Normalise to unit variance',

    'FEATTimeSeries.plotFullModelFit' : 'Plot full model fit',
    'FEATTimeSeries.plotEVs'          : 'Plot EV{} ({})',
    'FEATTimeSeries.plotPEFits'       : 'Plot PE{} fit ({})',
    'FEATTimeSeries.plotCOPEFits'     : 'Plot COPE{} fit ({})',
    'FEATTimeSeries.plotResiduals'    : 'Plot residuals',
    'FEATTimeSeries.plotPartial'      : 'Plot reduced data against',
    'FEATTimeSeries.plotData'         : 'Plot data',

    'OrthoEditProfile.mode'                   : 'Edit tool',
    'OrthoEditProfile.selectionSize'          : 'Selection size',
    'OrthoEditProfile.selectionIs3D'          : '3D selection',
    'OrthoEditProfile.fillValue'              : 'Fill value',
    'OrthoEditProfile.eraseValue'             : 'Erase value',
    'OrthoEditProfile.intensityThres'         : 'Intensity threshold',
    'OrthoEditProfile.intensityThresLimit'    : 'Intensity threshold limit',
    'OrthoEditProfile.localFill'              : 'Only select adjacent voxels',
    'OrthoEditProfile.limitToRadius'          : 'Only search within radius',
    'OrthoEditProfile.searchRadius'           : 'Search radius',
    'OrthoEditProfile.selectionOverlayColour' : 'Selection overlay',
    'OrthoEditProfile.selectionCursorColour'  : 'Selection cursor',
    'OrthoEditProfile.locationFollowsMouse'   : 'Location follows mouse',
    'OrthoEditProfile.showSelection'          : 'Show current selection',
    'OrthoEditProfile.drawMode'               : 'Draw mode',
    'OrthoEditProfile.targetImage'            : 'Target image',

    'Display.name'              : 'Overlay name',
    'Display.overlayType'       : 'Overlay data type',
    'Display.enabled'           : 'Enabled',
    'Display.alpha'             : 'Opacity',
    'Display.brightness'        : 'Brightness',
    'Display.contrast'          : 'Contrast',

    'NiftiOpts.transform'  : 'Image transform',
    'NiftiOpts.volume'     : 'Volume',

    'ColourMapOpts.displayRange'     : 'Display range',
    'ColourMapOpts.clippingRange'    : 'Clipping range',
    'ColourMapOpts.linkLowRanges'    : 'Link low display/clipping ranges',
    'ColourMapOpts.linkHighRanges'   : 'Link high display/clipping ranges',
    'ColourMapOpts.cmap'             : 'Colour map',
    'ColourMapOpts.cmapResolution'   : 'Colour map resolution',
    'ColourMapOpts.interpolateCmaps' : 'Interpolate colour maps',
    'ColourMapOpts.negativeCmap'     : '-ve colour map',
    'ColourMapOpts.useNegativeCmap'  : '-ve colour map',
    'ColourMapOpts.invert'           : 'Invert colour map',
    'ColourMapOpts.invertClipping'   : 'Invert clipping range',

    'VolumeOpts.clipImage'               : 'Clip by',
    'VolumeOpts.interpolation'           : 'Interpolation',
    'VolumeOpts.enableOverrideDataRange' : 'Override image data range',
    'VolumeOpts.overrideDataRange'       : 'Override image data range',

    'MaskOpts.colour'         : 'Colour',
    'MaskOpts.invert'         : 'Invert',
    'MaskOpts.threshold'      : 'Threshold',

    'VectorOpts.xColour'       : 'X Colour',
    'VectorOpts.yColour'       : 'Y Colour',
    'VectorOpts.zColour'       : 'Z Colour',

    'VectorOpts.suppressX'       : 'Suppress X value',
    'VectorOpts.suppressY'       : 'Suppress Y value',
    'VectorOpts.suppressZ'       : 'Suppress Z value',
    'VectorOpts.suppressMode'    : 'Suppression mode',
    'VectorOpts.colourImage'     : 'Colour by',
    'VectorOpts.cmap'            : 'Colour map',
    'VectorOpts.modulateImage'   : 'Modulate by',
    'VectorOpts.clipImage'       : 'Clip by',
    'VectorOpts.clippingRange'   : 'Clipping range',
    'VectorOpts.modulateRange'   : 'Modulation range',
    'VectorOpts.orientFlip'      : 'L/R orientation flip',

    'RGBVectorOpts.interpolation' : 'Interpolation',

    'LineVectorOpts.directed'    : 'Interpret vectors as directed',
    'LineVectorOpts.lineWidth'   : 'Line width',
    'LineVectorOpts.unitLength'  : 'Scale vectors to unit length',
    'LineVectorOpts.lengthScale' : 'Length scaling factor (%)',

    'MeshOpts.colour'          : 'Colour',
    'MeshOpts.outline'         : 'Show outline only',
    'MeshOpts.outlineWidth'    : 'Outline width',
    'MeshOpts.refImage'        : 'Reference image',
    'MeshOpts.coordSpace'      : 'Mesh coordinate space',
    'MeshOpts.vertexData'      : 'Vertex data',
    'MeshOpts.vertexDataIndex' : 'Vertex data index',
    'MeshOpts.showName'        : 'Show model name',
    'MeshOpts.lut'             : 'Lookup table',

    'LabelOpts.lut'          : 'Look-up table',
    'LabelOpts.outline'      : 'Show outline only',
    'LabelOpts.outlineWidth' : 'Outline width',
    'LabelOpts.showNames'    : 'Show label names',

    'TensorOpts.lighting'          : 'Lighting effects',
    'TensorOpts.tensorResolution'  : 'Ellipsoid quality',
    'TensorOpts.tensorScale'       : 'Tensor size',

    'SHOpts.lighting'        : 'Lighting effects',
    'SHOpts.size'            : 'FOD size',
    'SHOpts.radiusThreshold' : 'Radius threshold',
    'SHOpts.shResolution'    : 'FOD quality',
    'SHOpts.shOrder'         : 'Maximum SH order',
    'SHOpts.colourMode'      : 'Colour mode',
    'SHOpts.cmap'            : 'Radius colour map',
    'SHOpts.xColour'         : 'X direction colour',
    'SHOpts.yColour'         : 'Y direction colour',
    'SHOpts.zColour'         : 'Z direction colour',
})


choices = TypeDict({

    'DisplayContext.displaySpace' : {'world'  : 'World coordinates'},

    'SceneOpts.colourBarLocation'  : {'top'          : 'Top',
                                      'bottom'       : 'Bottom',
                                      'left'         : 'Left',
                                      'right'        : 'Right'},
    'SceneOpts.colourBarLabelSide' : {'top-left'     : 'Top / Left',
                                      'bottom-right' : 'Bottom / Right'},

    'SceneOpts.performance' : {1 : 'Fastest',
                               2 : 'Faster',
                               3 : 'Best looking'},

    'CanvasOpts.zax' : {0 : 'X axis',
                        1 : 'Y axis',
                        2 : 'Z axis'},

    'OrthoOpts.layout' : {'horizontal' : 'Horizontal',
                          'vertical'   : 'Vertical',
                          'grid'       : 'Grid'},

    'OrthoEditProfile.mode' : {'nav'    : 'Navigate',
                               'sel'    : 'Draw/select',
                               'desel'  : 'Erase/deselect',
                               'selint' : 'Select by intensity'},

    'CanvasPanel.movieAxis' : {0 : 'X',
                               1 : 'Y',
                               2 : 'Z',
                               3 : 'Time/volume'},

    'HistogramPanel.dataRange.min' : 'Min.',
    'HistogramPanel.dataRange.max' : 'Max.',

    'LightBoxOpts.zrange.min' : 'Min.',
    'LightBoxOpts.zrange.max' : 'Max.',

    'ColourMapOpts.displayRange.min' : 'Min.',
    'ColourMapOpts.displayRange.max' : 'Max.',

    'MaskOpts.threshold.min' : 'Min.',
    'MaskOpts.threshold.max' : 'Max.',

    'VectorOpts.displayType.line' : 'Lines',
    'VectorOpts.displayType.rgb'  : 'RGB',

    'VectorOpts.modulateImage.none' : 'No modulation',
    'VectorOpts.clipImage.none'     : 'No clipping',

    'VectorOpts.clippingRange.min' : 'Clip min.',
    'VectorOpts.clippingRange.max' : 'Clip max.',

    'VectorOpts.modulateRange.min' : 'Mod min.',
    'VectorOpts.modulateRange.max' : 'Mod max.',

    'VectorOpts.suppressMode' : {'white'       : 'White',
                                 'black'       : 'Black',
                                 'transparent' : 'Transparent'},

    'MeshOpts.refImage.none'     : 'No reference image',

    'MeshOpts.coordSpace' : {'affine'      : 'World coordinates',
                             'pixdim'      : 'Scaled voxels',
                             'pixdim-flip' : 'Scaled voxels forced to '
                                             'radiological orientation',
                             'id'          : 'Voxels'},

    'TensorOpts.tensorResolution.min' : 'Low',
    'TensorOpts.tensorResolution.max' : 'High',

    'NiftiOpts.transform' : {'affine'      : 'World coordinates',
                             'pixdim'      : 'Scaled voxels',
                             'pixdim-flip' : 'Radiological scaled voxels',
                             'id'          : 'Voxels',
                             'custom'      : 'Custom transformation'},

    'VolumeOpts.interpolation' : {'none'   : 'No interpolation',
                                  'linear' : 'Linear interpolation',
                                  'spline' : 'Spline interpolation'},


    'SHOpts.colourMode' : {'radius'    : 'Colour by radius',
                           'direction' : 'Colour by direction'},

    'Display.overlayType' : {'volume'     : '3D/4D volume',
                             'mask'       : '3D/4D mask image',
                             'label'      : 'Label image',
                             'rgbvector'  : '3-direction vector image (RGB)',
                             'linevector' : '3-direction vector image (Line)',
                             'mesh'       : '3D mesh',
                             'giftimesh'  : 'GIFTI surface',
                             'tensor'     : 'Diffusion tensor',
                             'sh'         : 'Diffusion SH'},

    'HistogramPanel.histType' : {'probability' : 'Probability',
                                 'count'       : 'Count'},

    'DataSeries.lineStyle' : {'-'  : 'Solid line',
                              '--' : 'Dashed line',
                              '-.' : 'Dash-dot line',
                              ':'  : 'Dotted line'},

    'TimeSeriesPanel.plotMode' : {'normal'        : 'Normal - no '
                                                    'scaling/offsets',
                                  'demean'        : 'Demeaned',
                                  'normalise'     : 'Normalised',
                                  'percentChange' : 'Percent changed'},
})


anatomy = TypeDict({

    ('Nifti', 'lowlong',   constants.ORIENT_A2P)               : 'Anterior',
    ('Nifti', 'lowlong',   constants.ORIENT_P2A)               : 'Posterior',
    ('Nifti', 'lowlong',   constants.ORIENT_L2R)               : 'Left',
    ('Nifti', 'lowlong',   constants.ORIENT_R2L)               : 'Right',
    ('Nifti', 'lowlong',   constants.ORIENT_I2S)               : 'Inferior',
    ('Nifti', 'lowlong',   constants.ORIENT_S2I)               : 'Superior',
    ('Nifti', 'lowlong',   constants.ORIENT_UNKNOWN)           : 'Unknown',
    ('Nifti', 'highlong',  constants.ORIENT_A2P)               : 'Posterior',
    ('Nifti', 'highlong',  constants.ORIENT_P2A)               : 'Anterior',
    ('Nifti', 'highlong',  constants.ORIENT_L2R)               : 'Right',
    ('Nifti', 'highlong',  constants.ORIENT_R2L)               : 'Left',
    ('Nifti', 'highlong',  constants.ORIENT_I2S)               : 'Superior',
    ('Nifti', 'highlong',  constants.ORIENT_S2I)               : 'Inferior',
    ('Nifti', 'highlong',  constants.ORIENT_UNKNOWN)           : 'Unknown',
    ('Nifti', 'lowshort',  constants.ORIENT_A2P)               : 'A',
    ('Nifti', 'lowshort',  constants.ORIENT_P2A)               : 'P',
    ('Nifti', 'lowshort',  constants.ORIENT_L2R)               : 'L',
    ('Nifti', 'lowshort',  constants.ORIENT_R2L)               : 'R',
    ('Nifti', 'lowshort',  constants.ORIENT_I2S)               : 'I',
    ('Nifti', 'lowshort',  constants.ORIENT_S2I)               : 'S',
    ('Nifti', 'lowshort',  constants.ORIENT_UNKNOWN)           : '?',
    ('Nifti', 'highshort', constants.ORIENT_A2P)               : 'P',
    ('Nifti', 'highshort', constants.ORIENT_P2A)               : 'A',
    ('Nifti', 'highshort', constants.ORIENT_L2R)               : 'R',
    ('Nifti', 'highshort', constants.ORIENT_R2L)               : 'L',
    ('Nifti', 'highshort', constants.ORIENT_I2S)               : 'S',
    ('Nifti', 'highshort', constants.ORIENT_S2I)               : 'I',
    ('Nifti', 'highshort', constants.ORIENT_UNKNOWN)           : '?',
    ('Nifti', 'space',     constants.NIFTI_XFORM_UNKNOWN)      : 'Unknown',
    ('Nifti', 'space',     constants.NIFTI_XFORM_SCANNER_ANAT) : 'Scanner '
                                                                 'anatomical',
    ('Nifti', 'space',     constants.NIFTI_XFORM_ALIGNED_ANAT) : 'Aligned '
                                                                 'anatomical',
    ('Nifti', 'space',     constants.NIFTI_XFORM_TALAIRACH)    : 'Talairach',
    ('Nifti', 'space',     constants.NIFTI_XFORM_MNI_152)      : 'MNI152',
    ('Nifti', 'space',     constants.NIFTI_XFORM_ANALYZE)      : 'ANALYZE',
})


nifti = TypeDict({

    'dimensions' : 'Number of dimensions',

    'datatype'    : 'Data type',
    'vox_units'   : 'XYZ units',
    'time_units'  : 'Time units',
    'descrip'     : 'Description',
    'aux_file'    : 'Auxillary file',
    'qform_code'  : 'QForm code',
    'sform_code'  : 'SForm code',
    'intent_code' : 'Intent code',
    'intent_name' : 'Intent name',

    'storageOrder'         : 'Storage order',
    'storageOrder.radio'   : 'Radiological',
    'storageOrder.neuro'   : 'Neurological',
    'storageOrder.unknown' : 'Unknown',

    'voxOrient.0'   : 'X voxel orientation',
    'voxOrient.1'   : 'Y voxel orientation',
    'voxOrient.2'   : 'Z voxel orientation',
    'worldOrient.0' : 'X world orientation',
    'worldOrient.1' : 'Y world orientation',
    'worldOrient.2' : 'Z world orientation',

    'transform' : 'Transformation matrix',
    'qform'     : 'QForm matrix',
    'sform'     : 'SForm matrix',
    'affine'    : 'Pixdim/origin matrix',

    'dim1' : 'dim1',
    'dim2' : 'dim2',
    'dim3' : 'dim3',
    'dim4' : 'dim4',
    'dim5' : 'dim5',
    'dim6' : 'dim6',
    'dim7' : 'dim7',

    'pixdim1' : 'pixdim1',
    'pixdim2' : 'pixdim2',
    'pixdim3' : 'pixdim3',
    'pixdim4' : 'pixdim4',
    'pixdim5' : 'pixdim5',
    'pixdim6' : 'pixdim6',
    'pixdim7' : 'pixdim7',

    'version.0' : 'ANALYZE',
    'version.1' : 'NIFTI1',
    'version.2' : 'NIFTI2',

    ('xyz_unit', 0)  : '[unknown units]',
    ('xyz_unit', 1)  : 'metres',
    ('xyz_unit', 2)  : 'mm',
    ('xyz_unit', 3)  : 'microns',
    ('t_unit',   0)  : '[unknown units]',
    ('t_unit',   8)  : 'seconds',
    ('t_unit',   16) : 'milliseconds',
    ('t_unit',   24) : 'microseconds',
    ('t_unit',   32) : 'hertz',
    ('t_unit',   40) : 'ppm',
    ('t_unit',   48) : 'radians/second',
    ('t_unit',  -1)  : 'volume',

    ('datatype', 0)    : 'UNKNOWN',
    ('datatype', 1)    : 'BINARY',
    ('datatype', 2)    : 'UINT8',
    ('datatype', 4)    : 'INT16',
    ('datatype', 8)    : 'INT32',
    ('datatype', 16)   : 'FLOAT32',
    ('datatype', 32)   : 'COMPLEX64',
    ('datatype', 64)   : 'DOUBLE64',
    ('datatype', 128)  : 'RGB',
    ('datatype', 255)  : 'ALL',
    ('datatype', 256)  : 'INT8',
    ('datatype', 512)  : 'UINT16',
    ('datatype', 768)  : 'UINT32',
    ('datatype', 1024) : 'INT64',
    ('datatype', 1280) : 'UINT64',
    ('datatype', 1536) : 'FLOAT128',
    ('datatype', 1792) : 'COMPLEX128',
    ('datatype', 2048) : 'COMPLEX256',
    ('datatype', 2304) : 'RGBA32',

    ('intent_code',  0)     :  'NIFTI_INTENT_CODE_NONE',
    ('intent_code',  2)     :  'NIFTI_INTENT_CODE_CORREL',
    ('intent_code',  3)     :  'NIFTI_INTENT_CODE_TTEST',
    ('intent_code',  4)     :  'NIFTI_INTENT_CODE_FTEST',
    ('intent_code',  5)     :  'NIFTI_INTENT_CODE_ZSCORE',
    ('intent_code',  6)     :  'NIFTI_INTENT_CODE_CHISQ',
    ('intent_code',  7)     :  'NIFTI_INTENT_CODE_BETA',
    ('intent_code',  8)     :  'NIFTI_INTENT_CODE_BINOM',
    ('intent_code',  9)     :  'NIFTI_INTENT_CODE_GAMMA',
    ('intent_code',  10)    :  'NIFTI_INTENT_CODE_POISSON',
    ('intent_code',  11)    :  'NIFTI_INTENT_CODE_NORMAL',
    ('intent_code',  12)    :  'NIFTI_INTENT_CODE_FTEST_NONC',
    ('intent_code',  13)    :  'NIFTI_INTENT_CODE_CHISQ_NONC',
    ('intent_code',  14)    :  'NIFTI_INTENT_CODE_LOGISTIC',
    ('intent_code',  15)    :  'NIFTI_INTENT_CODE_LAPLACE',
    ('intent_code',  16)    :  'NIFTI_INTENT_CODE_UNIFORM',
    ('intent_code',  17)    :  'NIFTI_INTENT_CODE_TTEST_NONC',
    ('intent_code',  18)    :  'NIFTI_INTENT_CODE_WEIBULL',
    ('intent_code',  19)    :  'NIFTI_INTENT_CODE_CHI',
    ('intent_code',  20)    :  'NIFTI_INTENT_CODE_INVGAUSS',
    ('intent_code',  21)    :  'NIFTI_INTENT_CODE_EXTVAL',
    ('intent_code',  22)    :  'NIFTI_INTENT_CODE_PVAL',
    ('intent_code',  23)    :  'NIFTI_INTENT_CODE_LOGPVAL',
    ('intent_code',  24)    :  'NIFTI_INTENT_CODE_LOG10)  :PVAL',
    ('intent_code',  1001)  :  'NIFTI_INTENT_CODE_ESTIMATE',
    ('intent_code',  1002)  :  'NIFTI_INTENT_CODE_LABEL',
    ('intent_code',  1003)  :  'NIFTI_INTENT_CODE_NEURONAME',
    ('intent_code',  1004)  :  'NIFTI_INTENT_CODE_GENMATRIX',
    ('intent_code',  1005)  :  'NIFTI_INTENT_CODE_SYMMATRIX',
    ('intent_code',  1006)  :  'NIFTI_INTENT_CODE_DISPVECT',
    ('intent_code',  1007)  :  'NIFTI_INTENT_CODE_VECTOR',
    ('intent_code',  1008)  :  'NIFTI_INTENT_CODE_POINTSET',
    ('intent_code',  1009)  :  'NIFTI_INTENT_CODE_TRIANGLE',
    ('intent_code',  1010)  :  'NIFTI_INTENT_CODE_QUATERNION',
    ('intent_code',  1011)  :  'NIFTI_INTENT_CODE_DIMLESS',
    ('intent_code',  2001)  :  'NIFTI_INTENT_CODE_TIME_SERIES',
    ('intent_code',  2002)  :  'NIFTI_INTENT_CODE_NODE_INDEX',
    ('intent_code',  2003)  :  'NIFTI_INTENT_CODE_RGB_VECTOR',
    ('intent_code',  2004)  :  'NIFTI_INTENT_CODE_RGBA_VECTOR',
    ('intent_code',  2005)  :  'NIFTI_INTENT_CODE_SHAPE',

    ###########################################
    # Non-standard (FSL-specific) intent codes.
    ###########################################

    # FNIRT
    ('intent_code',  2006)  :  'FSL_FNIRT_DISPLACEMENT_FIELD',
    ('intent_code',  2007)  :  'FSL_CUBIC_SPLINE_COEFFICIENTS',
    ('intent_code',  2008)  :  'FSL_DCT_COEFFICIENTS',
    ('intent_code',  2009)  :  'FSL_QUADRATIC_SPLINE_COEFFICIENTS',

    # TOPUP
    ('intent_code',  2016)  :  'FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS',
    ('intent_code',  2017)  :  'FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS',
    ('intent_code',  2018)  :  'FSL_TOPUP_FIELD',
})


feat = TypeDict({
    'analysisName'   : 'Analysis name',
    'analysisDir'    : 'Analysis directory',
    'partOfAnalysis' : 'Part of higher level analysis',
    'numPoints'      : 'Number of volumes',
    'numEVs'         : 'Number of EVs',
    'numContrasts'   : 'Number of contrasts',
    'report'         : 'Link to report',
})


melodic = TypeDict({
    'dataFile'       : 'Data file',
    'analysisDir'    : 'Analysis directory',
    'partOfAnalysis' : 'Part of higher level analysis',
    'numComponents'  : 'Number of ICs',
    'tr'             : 'TR time',
    'report'         : 'Link to report',
})

perspectives = {
    'default'  : 'Default layout',
    'melodic'  : 'MELODIC mode',
    'feat'     : 'FEAT mode',
    'ortho'    : 'Plain orthographic',
    'lightbox' : 'Plain lightbox',
}

tensor = {
    'v1' : 'First eigenvector image',
    'v2' : 'Second eigenvector image',
    'v3' : 'Third eigenvector image',
    'l1' : 'First eigenvalue image',
    'l2' : 'Second eigenvalue image',
    'l3' : 'Third eigenvalue image',
}


# Key format is "filename.colIndex"
plotLabels = {
    'prefiltered_func_data_mcf.par.0' : 'MCFLIRT X rotation (radians)',
    'prefiltered_func_data_mcf.par.1' : 'MCFLIRT Y rotation (radians)',
    'prefiltered_func_data_mcf.par.2' : 'MCFLIRT Z rotation (radians)',
    'prefiltered_func_data_mcf.par.3' : 'MCFLIRT X translation (mm)',
    'prefiltered_func_data_mcf.par.4' : 'MCFLIRT Y translation (mm)',
    'prefiltered_func_data_mcf.par.5' : 'MCFLIRT Z translation (mm)',

    'prefiltered_func_data_mcf_abs.rms.0' :
    'MCFLIRT absolute mean displacement (mm)',
    'prefiltered_func_data_mcf_rel.rms.0' :
    'MCFLIRT relative mean displacement (mm)',
}


about = {
    'title'      : 'About FSLeyes',
    'author'     : 'Paul McCarthy',
    'email'      : 'paulmc@fmrib.ox.ac.uk',
    'company'    : 'FMRIB Centre, Oxford, UK',
    'version'    : 'FSLeyes version: {}',
    'vcsVersion' : 'Internal version: {}',
    'glVersion'  : 'OpenGL version: {}',
    'glCompat'   : 'OpenGL compatibility: {}',
    'glRenderer' : 'OpenGL renderer: {}',
    'fslVersion' : 'FSL version: {}',
    'fslPath'    : 'FSL directory: {}',
    'software'   : textwrap.dedent(
    u"""
    FSLeyes was developed at the FMRIB Centre, Nuffield Department of Clinical Neurosciences, Oxford University, United Kingdom.

    FSLeyes is a Python application which leverages the following open-source software libraries:

     - indexed_gzip [0.3.3] (https://github.com/pauldmccarthy/indexed_gzip/)
     - jinja2 [{}] (http://jinja.pocoo.org)
     - matplotlib [{}] (http://www.matplotlib.org)
     - nibabel [{}] (http://nipy.org/nibabel)
     - numpy [{}] (http://www.numpy.org)
     - pillow [{}]  (http://python-pillow.org/)
     - fsleyes-props [{}] (https://git.fmrib.ox.ac.uk/paulmc/fsleyes-props)
     - fsleyes-widgets [{}] (https://git.fmrib.ox.ac.uk/paulmc/fsleyes-widgets)
     - fslpy [{}] (https://git.fmrib.ox.ac.uk/paulmc/fslpy)
     - pyopengl [{}] (http://pyopengl.sourceforge.net)
     - pyparsing [{}] (http://pyparsing.wikispaces.com/)
     - scipy [{}] (http://www.scipy.org)
     - six [{}] (https://pythonhosted.org/six/)
     - trimesh [{}] (https://github.com/mikedh/trimesh)
     - wxPython [{}] (http://www.wxpython.org)

    Cubic/spline interpolation routines used in FSLeyes are provided by Daniel Ruijters and Philippe Th\u00E9venaz, described at http://www.dannyruijters.nl/cubicinterpolation/.

    Some of the icons used in FSLeyes are derived from the Freeline icon set, by Enes Dal, available at https://www.iconfinder.com/Enesdal, and released under the Creative Commons (Attribution 3.0 Unported) license.

    FSLeyes is released under Version 2.0 of the Apache Software License.

    Copyright 2016-2017 University of Oxford, Oxford, UK.
    """).strip(),

    # This is a list of all the libraries listed
    # in the software string above - the AboutDialog
    # dynamically looks up the version number for
    # each of them, and inserts them into the above
    # string.
    'libs' : [                 'jinja2',             'matplotlib',
              'nibabel',       'numpy',              'PIL',
              'fsleyes_props', 'fsleyes_widgets',    'fsl',
              'OpenGL',        'pyparsing',          'scipy',
              'six',           'fsleyes.gl.trimesh', 'wx'],
}
