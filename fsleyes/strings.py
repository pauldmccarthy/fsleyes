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

from fsl.utils.typedict import TypeDict
import fsl.data.constants as constants


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

    'SaveOverlayAction.overwrite'      : 'Do you want to overwrite {}, or '
                                         'save the image to a new file?',

    'loadOverlays.loading'     : 'Loading {} ...',
    'loadOverlays.error'       : 'An error occurred loading the image '
                                         '{}\n\nDetails: {} - {}',

    'loadOverlays.unknownType' : 'Unknown data type',

    'actions.loadcolourmap.loadcmap'    : 'Open colour map file',
    'actions.loadcolourmap.namecmap'    : 'Enter a name for the colour map - '
                                          'please use only letters, numbers, '
                                          'and underscores.',
    'actions.loadcolourmap.installcmap' : 'Do you want to install '
                                          'this colour map permanently?',
    'actions.loadcolourmap.alreadyinstalled' : 'A colour map with that name '
                                               'already exists - choose a '
                                               'different name.',
    'actions.loadcolourmap.invalidname'      : 'Please use only letters, '
                                               'numbers, and underscores.',
    'actions.loadcolourmap.installerror'     : 'An error occurred while '
                                               'installing the colour map. ',

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
    'CanvasPanel.screenshot.error'      : 'Sorry, there was an error '
                                          'saving the screenshot. Try '
                                          'calling render directly with '
                                          'this command: \n{}',

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

    'NewLutDialog.newLut' : 'Enter a name for the new LUT',

    'ClusterPanel.noOverlays'     : 'Add a FEAT overlay',
    'ClusterPanel.notFEAT'        : 'Choose a FEAT overlay',
    'ClusterPanel.noClusters'     : 'No cluster results exist '
                                    'in this FEAT analysis',
    'ClusterPanel.badData'        : 'Cluster data could not be parsed - '
                                    'check your cluster_*.txt files.',
    'ClusterPanel.loadingCluster' : 'Loading clusters for COPE{} ({}) ...',

    'OrthoEditProfile.imageChange'        : 'You are now editing {}. ',
    'OrthoEditProfile.imageChangeHint'    : 'Setting {} as the display '
                                            'space reference\nimage - the '
                                            'display space must match the '
                                            'image being edited.', 
    
    'OrthoEditProfile.imageChange.suppress' : 'Do not show this '
                                              'message again',

    'MelodicClassificationPanel.disabled'    : 'Choose a melodic image.',
    'MelodicClassificationPanel.loadError'   : 'An error occurred while '
                                               'loading the file {}.'
                                               '\n\nDetails: {}',
    'MelodicClassificationPanel.noMelDir'    : 'The label file {} does not '
                                               'specify a path to a Melodic '
                                               'directory!',
    'MelodicClassificationPanel.saveError'   : 'An error occurred while '
                                               'saving the file {}.'
                                               '\n\nDetails: {}', 
    'MelodicClassificationPanel.wrongNComps' : 'The mumber of components in '
                                               'the label file {} is greater '
                                               'than the number of components '
                                               'in the overlay {}!',
    'MelodicClassificationPanel.diffMelDir'  : 'The label file {} does not '
                                               'refer to the melodic '
                                               'directory of the selected '
                                               'overlay ({}). What do you '
                                               'want to do?',
    
    'MelodicClassificationPanel.diffMelDir.labels'  : 'Load the overlay in '
                                                      'the label file',
    'MelodicClassificationPanel.diffMelDir.overlay' : 'Apply the labels to '
                                                      'the current overlay',

    'SaveOverlayAction.saveError' :
    'An error occurred while saving the file {}.\n\nDetails: {} - {}',

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
    'An error occurred loading the atlas specification {}\n\nDetails: {}', 

    'CorrelateAction.calculating' :
    'Calculating correlation values for seed voxel [{}, {}, {}] ...',
})


titles = TypeDict({
    
    'interactiveLoadOverlays.fileDialog' : 'Open overlay files',
    'interactiveLoadOverlays.dirDialog'  : 'Open overlay directories',
    
    'loadOverlays.error'  : 'Error loading overlay',

    'FSLeyesFrame.saveLayout'      : 'Save layout',
    'FSLeyesFrame.unsavedOverlays' : 'Unsaved images',
 
    
    'OrthoPanel'         : 'Ortho View',
    'LightBoxPanel'      : 'Lightbox View',
    'TimeSeriesPanel'    : 'Time series',
    'PowerSpectrumPanel' : 'Power spectra',
    'HistogramPanel'     : 'Histogram',
    'ShellPanel'         : 'Python shell',
 

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
    'NewLutDialog'              : 'New LUT',

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

    'LookupTablePanel.loadLut'     : 'Select a lookup table file',
    'LookupTablePanel.labelExists' : 'Label already exists',

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

    'OrthoEditProfile.imageChange'        : 'Changing edited image',

    'ImportDataSeriesAction.error'        : 'Error loading file',
    'ImportDataSeriesAction.selectXScale' : 'X axis scaling factor',

    'ExportDataSeriesAction.saveXColumn'  : 'Save X data?',

    'LoadAtlasAction.fileDialog'  : 'Load XML atlas specification',
    'LoadAtlasAction.error'       : 'Error loading atlas specification',

    'LoadColourMapAction.installcmap'     : 'Install colour map?',
})


actions = TypeDict({

    'LoadOverlayAction'        : 'Add overlay from file',
    'LoadOverlayFromDirAction' : 'Add overlay from directory',
    'LoadStandardAction'       : 'Add standard',
    'CopyOverlayAction'        : 'Copy',
    'LoadAtlasAction'          : 'Add atlas',
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


    'CanvasPanel.screenshot'                : 'Take screenshot',
    'CanvasPanel.showCommandLineArgs'       : 'Show command line for scene',
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
    
    'OrthoPanel.toggleOrthoToolBar'     : 'Ortho toolbar',
    'OrthoPanel.toggleEditMode'         : 'Edit mode',
    'OrthoPanel.toggleEditPanel'        : 'Edit settings panel',
    'OrthoPanel.resetDisplay'           : 'Reset display',
    'OrthoPanel.centreCursor'           : 'Centre cursor',
    'OrthoPanel.centreCursorWorld'      : 'Centre cursor at (0, 0, 0)',

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

    'LutLabelDialog.value'    : 'Value',
    'LutLabelDialog.name'     : 'Name',
    'LutLabelDialog.colour'   : 'Colour',
    'LutLabelDialog.ok'       : 'Ok',
    'LutLabelDialog.cancel'   : 'Cancel',
    'LutLabelDialog.newLabel' : 'New label',

    'NewLutDialog.ok'     : 'Ok',
    'NewLutDialog.cancel' : 'Cancel',
    'NewLutDialog.newLut' : 'New LUT',


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
    'OverlayDisplayPanel.ModelOpts'      : 'Model settings',
    'OverlayDisplayPanel.TensorOpts'     : 'Diffusion tensor settings',
    'OverlayDisplayPanel.SHOpts'         : 'Diffusion SH settings',
    
    'OverlayDisplayPanel.loadCmap'       : 'Load colour map',

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
    
    
    'OverlayInfoPanel.Image'                    : 'NIFTI image',
    'OverlayInfoPanel.FEATImage'                : 'NIFTI image '
                                                  '(FEAT analysis)',
    'OverlayInfoPanel.FEATImage.featInfo'       : 'FEAT information',
    'OverlayInfoPanel.MelodicImage'             : 'NIFTI image '
                                                  '(MELODIC analysis)', 
    'OverlayInfoPanel.MelodicImage.melodicInfo' : 'MELODIC information',
    
    'OverlayInfoPanel.Model'                        : 'VTK model',
    'OverlayInfoPanel.Model.numVertices'            : 'Number of vertices',
    'OverlayInfoPanel.Model.numIndices'             : 'Number of indices',
    'OverlayInfoPanel.Model.displaySpace'           : 'Display space',
    'OverlayInfoPanel.Model.refImage'               : 'Reference image',
    'OverlayInfoPanel.Model.coordSpace'             : 'Vertices defined in',
    'OverlayInfoPanel.Model.coordSpace.id'          : 'Voxels ({})',
    'OverlayInfoPanel.Model.coordSpace.pixdim'      : 'Scaled voxels ({})',
    'OverlayInfoPanel.Model.coordSpace.pixdim-flip' : 'Scaled voxels [FSL '
                                                      'convention] ({})',
    'OverlayInfoPanel.Model.coordSpace.affine'      : 'World coordinates ({})',
    'OverlayInfoPanel.Model.coordSpace.display'     : 'Display coordinate '
                                                      'system',
    
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
    'OrthoOpts.labelSize'   : 'Label size (%)',
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

    'NiftiOpts.resolution' : 'Resolution',
    'NiftiOpts.transform'  : 'Image transform',
    'NiftiOpts.volume'     : 'Volume',
    
    'VolumeOpts.displayRange'    : 'Display range',
    'VolumeOpts.clippingRange'   : 'Clipping range',
    'VolumeOpts.clipImage'       : 'Clip by',
    'VolumeOpts.linkLowRanges'   : 'Link low display/clipping ranges',
    'VolumeOpts.linkHighRanges'  : 'Link high display/clipping ranges',
    'VolumeOpts.cmap'            : 'Colour map',
    'VolumeOpts.cmapResolution'  : 'Colour map resolution',
    'VolumeOpts.negativeCmap'    : '-ve colour map',
    'VolumeOpts.useNegativeCmap' : '-ve colour map',
    'VolumeOpts.invert'          : 'Invert colour map',
    'VolumeOpts.invertClipping'  : 'Invert clipping range',
    'VolumeOpts.interpolation'   : 'Interpolation',
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

    'ModelOpts.colour'       : 'Colour',
    'ModelOpts.outline'      : 'Show outline only',
    'ModelOpts.outlineWidth' : 'Outline width',
    'ModelOpts.refImage'     : 'Reference image',
    'ModelOpts.coordSpace'   : 'Model coordinate space',
    'ModelOpts.showName'     : 'Show model name',

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

    'VolumeOpts.displayRange.min' : 'Min.',
    'VolumeOpts.displayRange.max' : 'Max.',

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

    'ModelOpts.refImage.none'     : 'No reference image',

    'ModelOpts.coordSpace' : {'affine'      : 'World coordinates',
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
                             'model'      : '3D model',
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

    'storageOrder'       : 'Storage order',
    'storageOrder.radio' : 'Radiological',
    'storageOrder.neuro' : 'Neurological',

    'voxOrient.0'   : 'X voxel orientation',
    'voxOrient.1'   : 'Y voxel orientation',
    'voxOrient.2'   : 'Z voxel orientation',
    'worldOrient.0' : 'X world orientation',
    'worldOrient.1' : 'Y world orientation',
    'worldOrient.2' : 'Z world orientation',

    'qform' : 'QForm matrix',
    'sform' : 'SForm matrix',

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
    ('intent_code',  2)     :  'NIFTI_FIRST_STATCODE',
    ('intent_code',  24)    :  'NIFTI_LAST_STATCODE',
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

    'prefiltered_func_data_mcf_abs.rms.0' : 'MCFLIRT absolute mean displacement (mm)',
    'prefiltered_func_data_mcf_rel.rms.0' : 'MCFLIRT relative mean displacement (mm)',
}


about = {
    'title'      : 'About FSLeyes',
    'author'     : 'Paul McCarthy',
    'email'      : 'paulmc@fmrib.ox.ac.uk',
    'company'    : u'\u00A9 FMRIB Centre, Oxford, UK',
    'version'    : 'FSLeyes version: {}',
    'vcsVersion' : 'Internal version: {}',
    'glVersion'  : 'OpenGL version: {}',
    'glCompat'   : 'OpenGL compatibility: {}',
    'glRenderer' : 'OpenGL renderer: {}',
    'software'   : textwrap.dedent(
    """
    FSLeyes was developed at the FMRIB Centre, Nuffield Department of Clinical Neurosciences, Oxford University, United Kingdom.
    
    FSLeyes is a Python application which leverages the following open-source software libraries:

     - indexed_gzip [{}] (https://github.com/pauldmccarthy/indexed_gzip/)
     - jinja2 [{}] (http://jinja.pocoo.org)
     - matplotlib [{}] (http://www.matplotlib.org)
     - nibabel [{}] (http://nipy.org/nibabel)
     - numpy [{}] (http://www.numpy.org)
     - pillow [{}]  (http://python-pillow.org/)
     - props [{}] (https://git.fmrib.ox.ac.uk/paulmc/props)
     - fslpy [{}] (https://git.fmrib.ox.ac.uk/paulmc/fslpy)
     - pyopengl [{}] (http://pyopengl.sourceforge.net)
     - pyparsing [{}] (http://pyparsing.wikispaces.com/)
     - scipy [{}] (http://www.scipy.org)
     - six [{}] (https://pythonhosted.org/six/)
     - wxPython [{}] (http://www.wxpython.org)
    
    Some of the icons used in FSLeyes are derived from the Freeline icon set, by Enes Dal, available at https://www.iconfinder.com/Enesdal, and released under the Creative Commons (Attribution 3.0 Unported) license.
    """).strip(),

    # This is a list of all the libraries listed
    # in the software string above - the AboutDialog
    # dynamically looks up the version number for
    # each of them, and inserts them into the above
    # string.
    'libs' : ['indexed_gzip', 'jinja2',    'matplotlib',
              'nibabel',      'numpy',     'PIL',
              'props',        'fsl',       'OpenGL',
              'pyparsing',    'scipy',     'six',
              'wx'],
}
