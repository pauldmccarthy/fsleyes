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
 :data:`layouts`      Layout labels.
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

    'main.parseArgs.error' :
    'An error occurred loading the command-line arguments.',

    'FSLeyesFrame.restoringLayout'     : 'Restoring layout from last '
                                         'session ...',
    'FSLeyesFrame.saveLayout'          : 'Save this layout for next time?',
    'FSLeyesFrame.dontAskToSaveLayout' : 'Never ask me again',
    'FSLeyesFrame.unsavedOverlays'     : 'You have unsaved images - are '
                                         'you sure you want to exit?',

    'layout.applyingLayout' : 'Applying {} layout ...',

    'SaveLayoutAction.enterName' :
    'Enter a name for the layout',
    'SaveLayoutAction.nameIsBuiltIn' :
    '"{}" is a reserved layout name - enter a different name.',
    'SaveLayoutAction.confirmOverwrite' :
    'A layout with the name "{}" already exists - do '
    'you want to replace it?',

    'ClearLayoutsAction.confirmClear' : 'All saved layouts will be '
                                        'cleared! Are you sure you want '
                                        'to continue?',

    'FSLeyesApp.openURLError' : 'An error occurred loading the URL.',

    'SliceCanvas.globjectError'  :
    'An error occurred initialising the display for {}',

    'Texture.dataError'  :
    'An error occurred updating the texture data',

    'SaveOverlayAction.overwrite'      : 'Do you want to overwrite {}, or '
                                         'save the image to a new file?',

    'loadOverlays.loading'     : 'Loading {} ...',
    'loadOverlays.error'       : 'An error occurred loading the image {}',

    'loadOverlays.unknownType' : 'Unknown data type',

    'LocationInfoPanel.displaySpaceWarning' :
    'Displaying images with different orientations/fields of view!',

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
    'LookupTablePanel.labelExists' :
    'The {} LUT already contains a label with value {}',
    'LookupTablePanel.loadError' :
    'An error occurred while loading {}',

    'actions.copyoverlay.createMask'  : 'Create empty mask image '
                                        'with same dimensions',
    'actions.copyoverlay.copyDisplay' : 'Copy display properties',
    'actions.copyoverlay.copy4D'      : 'Copy 4D image',
    'actions.copyoverlay.copyMulti'   : 'Copy all channels/components',
    'actions.copyoverlay.component'   :
    'Select the component/channel you want to copy',

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
    'AtlasInfoPanel.noOverlays'    : 'Load an image!',

    'AtlasInfoPanel.loadAtlasError' : 'An error occurred while trying '
                                      'to load the atlas "{}":\nDetails: {}',

    'CanvasPanel.showCommandLineArgs.title'   : 'Scene parameters',
    'CanvasPanel.showCommandLineArgs.message' : 'Use these parameters on the '
                                                'command line to recreate '
                                                'the current scene',
    'CanvasPanel.showCommandLineArgs.unsaved' :
    'All of your images must be saved to a file before a command line can be '
    'generated!',

    'PlotCanvas.preparingData'          : 'Preparing data - please wait...',

    'HistogramPanel.calcHist'           : 'Calculating histogram for {} ...',

    'ClusterPanel.noOverlays'     : 'Add a FEAT overlay',
    'ClusterPanel.notFEAT'        : 'Choose a FEAT overlay',
    'ClusterPanel.noClusters'     : 'No cluster results exist '
                                    'in this FEAT analysis',
    'ClusterPanel.badData'        : 'Cluster data could not be parsed - '
                                    'check your cluster_*.txt files.',
    'ClusterPanel.loadingCluster' : 'Loading clusters for COPE{} ({}) ...',

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


    'ScreenshotAction.screenshot' : 'Save screenshot',
    'ScreenshotAction.pleaseWait' : 'Saving screenshot to {}...',
    'ScreenshotAction.error'      : 'An error occurred saving the screenshot.',

    'MovieGifAction.movieGif'     : 'Save animated GIF',

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

    'AddMaskDataSeriesAction.selectMask'  :
    'Choose an ROI mask to extract the time series data (mean across\n'
    'voxels, optionally weighted by mask values) from {}:',

    'AddMaskDataSeriesAction.weighted'  :
    'Calculate weighted mean using the ROI mask voxel values as weights',

    'AddROIHistogramAction.selectMask' :
    'Choose an ROI mask to plot the histogram from {} for:',

    'LoadAtlasAction.error'       :
    'An error occurred loading the atlas specification {}.',

    'ClearSettingsAction.confirm' :
    'Are you sure you want to clear all FSLeyes settings? All preferences, '
    'saved layouts, colour maps, lookup tables, and loaded atlases will '
    'be lost!\n\nYou will need to restart FSLeyes for some changes to take '
    'effect.',

    'CorrelateAction.calculating' :
    'Calculating correlation values for seed voxel [{}, {}, {}] ...',

    'EditTransformPanel.saveFlirt.error' :
    'An error occurred saving the affine matrix.',

    'SaveFlirtXfmAction.error' :
    'An error occurred saving the affine matrix.',

    'FlirtFileDialog.matFile'    : 'Select affine transformation matrix file',
    'FlirtFileDialog.refFile'    : 'Select FLIRT reference image',

    'CropImagePanel.saveCrop'  : 'Select a file to save the crop parameters',
    'CropImagePanel.loadCrop'  : 'Select a file to load crop parameters from',
    'CropImagePanel.saveError' :
    'An error occurred saving the crop parameters',
    'CropImagePanel.loadError' :
    'An error occurred loading the crop parameters',
    'CropImagePanel.dsWarning' :
    'Warning: To crop an image, you must select it\n'
    'as the display space. You can change the display\n'
    'space back in the view settings panel.',

    'LocationHistoryPanel.load' : 'Select a location file to load',
    'LocationHistoryPanel.save' : 'Select a file to save the locations to',
    'LocationHistoryPanel.loadError' :
    'An error occurred loading locations from {}',
    'LocationHistoryPanel.saveError' :
    'An error occurred saving locations to {}',

    'OrthoEditToolBar.dsWarning' :
    'Warning: You must set the display\n'
    'space to the image being edited!',

    'LoadVertexDataAction.loadVertexData' :
    'Select a vertex data file for {}',

    'LoadVertexDataAction.loadVertices' :
    'Select a vertex file for {}',

    'LoadVertexDataAction.error' :
    'An error occurred while loading the vertex data for {}',

    'UpdateCheckAction.newVersionAvailable' :
    'A new version of FSLeyes is available. This version\n'
    'of FSLeyes is {}, and the latest is {}.',

    'UpdateCheckAction.upToDate' :
    'Your version of FSLeyes ({}) is up to date.',

    'UpdateCheckAction.updateUrl' :
    'The latest version of FSLeyes is available from:',

    'UpdateCheckAction.newVersionError' :
    'An error occurred while checking for FSLeyes updates. Try again later.',

    'ApplyCommandLineAction.apply' :
    'Type/paste FSLeyes command line arguments into the field below.',

    'ApplyCommandLineAction.error' :
    'An error occurred while applying the command line arguments.',

    'loadDicom.selectDir' : 'Select DICOM directory',
    'loadDicom.scanning'  : 'Scanning for DICOM data series...',
    'loadDicom.loading'   : 'Loading DICOM data series...',
    'loadDicom.scanError' :
    'An error occurred while scanning the DICOM directory',
    'loadDicom.loadError' :
    'An error occurred while loading DICOM data',

    'NotebookAction.init.kernel' : 'Initialising IPython kernel...',
    'NotebookAction.init.server' : 'Starting Jupyter notebook server...',
    'NotebookAction.init.error' :
    'An error occurred initialising IPython/Jupyter! ',

    'LoadPluginAction.loadPlugin' :
    'Choose a FSLeyes plugin file',
    'LoadPluginAction.installPlugin' :
    'Do you want to install this plugin permanently?',
    'LoadPluginAction.loadError'  :
    'An error occurred loading the plugin file.',
    'LoadPluginAction.installError'  :
    'An error occurred installing the plugin file.',

    'FileTreePanel.loadDir'        : 'Load directory',
    'FileTreePanel.loadCustomTree' : 'Load filetree file',
    'FileTreePanel.save'           : 'Save notes',
    'FileListPanel.buildingList'   : 'Building file list ...',
    'FileListPanel.loading'        : 'Loading files ...',

    'ProjectImageToSurfaceAction.noOverlap' :
    'Cannot identify any loaded images which overlap with the surface in '
    'the display coordinate system.',

    'OrthoAnnotateProfile.TextAnnotation' : 'Enter your text',

    'SaveAnnotationsAction.saveFile' :
    'Save annotations to file',
    'SaveAnnotationsAction.saveFileError' :
    'An errror occurred while saving the file.',
    'LoadAnnotationsAction.loadFile' :
    'Load annotations from file',
    'LoadAnnotationsAction.loadFileError' :
    'An errror occurred while loading the file.',

    'SampleLinePanel.exportError'  :
    'An error occurred exporting the data!',
})


titles = TypeDict({

    'interactiveLoadOverlays.fileDialog' : 'Open overlay files',
    'interactiveLoadOverlays.dirDialog'  : 'Open overlay directories',

    'loadOverlays.error'  : 'Error loading overlay',

    'main.parseArgs.error' : 'Error loading command line arguments',

    'FSLeyesFrame.saveLayout'      : 'Save layout',
    'FSLeyesFrame.unsavedOverlays' : 'Unsaved images',
    'FSLeyesFrame.setFSLDIR'       : 'Select FSL installation directory',

    'FSLeyesApp.openURLError' : 'Error loading URL',

    'OrthoPanel'         : 'Ortho View',
    'LightBoxPanel'      : 'Lightbox View',
    'Scene3DPanel'       : '3D View',
    'TimeSeriesPanel'    : 'Time series',
    'PowerSpectrumPanel' : 'Power spectra',
    'HistogramPanel'     : 'Histogram',
    'ShellPanel'         : 'Python shell',

    'SliceCanvas.globjectError'  : 'Error initialising display',
    'Texture.dataError'          : 'Error updating data',


    'AtlasInfoPanel'       : 'Atlas information',
    'AtlasOverlayPanel'    : 'Atlas search',
    'AtlasManagementPanel' : 'Atlas management',

    'OverlayListPanel'          : 'Overlay list',
    'AtlasPanel'                : 'Atlases',
    'LocationPanel'             : 'Location',
    'OverlayDisplayToolBar'     : 'Overlay display toolbar',
    'CanvasSettingsPanel'       : 'View settings',
    'OverlayDisplayPanel'       : 'Overlay display settings',
    'OrthoToolBar'              : 'Ortho toolbar',
    'OrthoEditToolBar'          : 'Ortho view edit toolbar',
    'OrthoEditActionToolBar'    : 'Ortho view edit action toolbar',
    'OrthoEditSettingsPanel'    : 'Ortho view edit settings',
    'LightBoxToolBar'           : 'Lightbox toolbar',
    'LookupTablePanel'          : 'Lookup tables',
    'LutLabelDialog'            : 'New LUT label',
    'Scene3DToolBar'            : '3D toolbar',
    'AnnotationPanel'           : 'Annotations',
    'FlirtFileDialog.load'      : 'Load affine transformation',
    'FlirtFileDialog.save'      : 'Save affine transformation',

    'NewImageDialog'            : 'New image',

    'PlotListPanel'             : 'Plot list',
    'TimeSeriesControlPanel'    : 'Time series control',
    'HistogramControlPanel'     : 'Histogram control',
    'PowerSpectrumControlPanel' : 'Power spectrum control',
    'ClusterPanel'              : 'Cluster browser',
    'OverlayInfoPanel'          : 'Overlay information',
    'PlotToolBar'               : 'Plot toolbar',
    'TimeSeriesToolBar'         : 'Time series toolbar',
    'HistogramToolBar'          : 'Histogram toolbar',
    'PowerSpectrumToolBar'      : 'Power spectrum toolbar',

    'MelodicClassificationPanel' : 'Melodic IC classification',

    'CropImagePanel'             : 'Crop',
    'EditTransformPanel'         : 'Nudge',
    'SampleLinePanel'            : 'Sample along line',

    'FileTreePanel'              : 'File tree',

    'LocationHistoryPanel.loadError' : 'Error loading location file',
    'LocationHistoryPanel.saveError' : 'Error saving location file',

    'LookupTablePanel.newlut'       : 'Name lookup table',
    'LookupTablePanel.loadLut'      : 'Select a lookup table file',
    'LookupTablePanel.labelExists'  : 'Label already exists',
    'LookupTablePanel.installerror' : 'Error installing lookup table',
    'LookupTablePanel.loadError'    : 'Error loading lut file',

    'MelodicClassificationPanel.loadDialog' : 'Load FIX/Melview file...',
    'MelodicClassificationPanel.saveDialog' : 'Save FIX/Melview file...',
    'MelodicClassificationPanel.loadError'  : 'Error loading FIX/Melview file',
    'MelodicClassificationPanel.saveError'  : 'Error saving FIX/Melview file',

    'ScreenshotAction.screenshot'          : 'Save screenshot',
    'ScreenshotAction.error'               : 'Error saving screenshot',
    'ClearLayoutsAction.confirmClear'      : 'Clear all layouts?',
    'DiagnosticReportAction.saveReport'    : 'Save diagnostic report',
    'SaveOverlayAction.overwrite'          : 'Overwrite existing file?',
    'SaveOverlayAction.saveFile'           : 'Save overlay to file',
    'SaveOverlayAction.saveError'          : 'Error saving file',

    'RemoveAllOverlaysAction.unsavedOverlays' : 'Unsaved images',

    'removeoverlay.unsaved' : 'Remove unsaved image?',
    'reloadoverlay.unsaved' : 'Reload unsaved image?',

    'actions.copyoverlay.component' : 'Select component/channel',

    'OrthoPanel.toolMenu'                 : 'Tools',

    'OrthoEditProfile.imageChange'        : 'Changing edited image',
    'OrthoCropProfile.imageChange'        : 'Changing cropped image',

    'ImportDataSeriesAction.error'        : 'Error loading file',
    'ImportDataSeriesAction.selectXScale' : 'X axis scaling factor',

    'ExportDataSeriesAction.saveXColumn'  : 'Save X data?',

    'CropImagePanel.loadError' : 'Error loading crop parameters',
    'CropImagePanel.saveError' : 'Error saving crop parameters',

    'AddMaskDataSeriesAction.selectMask'  :
    'ROI time series from {}',

    'AddROIHistogramAction.selectMask'  :
    'ROI histogram from {}',

    'LoadAtlasAction.fileDialog'  : 'Load XML atlas specification',
    'LoadAtlasAction.error'       : 'Error loading atlas specification',

    'LoadVertexDataAction.error' : 'Error loading vertex data',

    'SaveFlirtXfmAction.error' : 'Error saving affine matrix',

    'ClearSettingsAction.confirm' : 'Clear all settings?',

    'CanvasPanel.showCommandLineArgs.unsaved' : 'Unsaved images',


    'LoadColourMapAction.namecmap'        : 'Name colour map.',
    'LoadColourMapAction.installcmap'     : 'Install colour map?',
    'LoadColourMapAction.installerror'    : 'Error installing colour map',

    'UpdateCheckAction.upToDate'            : 'FSLeyes is up to date',
    'UpdateCheckAction.newVersionAvailable' : 'New version available',
    'UpdateCheckAction.newVersionError'     : 'Error checking for updates',

    'ApplyCommandLineAction.title' : 'Apply FSLeyes command line',
    'ApplyCommandLineAction.error' : 'Error applying command line',

    'XNATBrowser' : 'Open from XNAT repository',

    'loadDicom.scanning'  : 'Scanning DICOM directory',
    'loadDicom.loading'   : 'Loading DICOM data series',
    'loadDicom.scanError' : 'Error reading DICOM directory',
    'loadDicom.loadError' : 'Error loading DICOM series',
    'BrowseDicomDialog'   : 'Select DICOM series',

    'NotebookAction.init' : 'Starting Jupyter',
    'NotebookAction.init.error' :
    'Error initialising IPython/Jupyter',

    'LoadPluginAction.loadError'     : 'Error loading plugin file',
    'LoadPluginAction.installPlugin' : 'Install plugin?',
    'LoadPluginAction.installError'  : 'Error installing plugin file',

    'ProjectImageToSurfaceAction.dialog'  : 'Select image',

    'SaveAnnotationsAction.saveFileError' : 'Error saving file',
    'LoadAnnotationsAction.loadFileError' : 'Error loading file',

    'SampleLinePanel.savefile' : 'Select file to save sampled data to',
    'SampleLinePanel.exportError'  : 'Error saving file',
    'ExportSampledDataDialog'  : 'Export sampled data to file',
})


actions = TypeDict({

    'LoadOverlayAction'           : 'Add from file',
    'LoadOverlayFromDirAction'    : 'Add from directory',
    'LoadStandardAction'          : 'Add standard',
    'LoadDicomAction'             : 'Add from DICOM',
    'BrowseXNATAction'            : 'Add from XNAT',
    'NewImageAction'              : 'New image',
    'CopyOverlayAction'           : 'Copy',
    'LoadAtlasAction'             : 'Import new atlas',
    'ClearSettingsAction'         : 'Clear FSLeyes settings',
    'UpdateCheckAction'           : 'Check for updates',
    'SaveOverlayAction'           : 'Save',
    'ReloadOverlayAction'         : 'Reload',
    'RemoveOverlayAction'         : 'Remove',
    'RemoveAllOverlaysAction'     : 'Remove all',
    'LoadColourMapAction'         : 'Load custom colour map',
    'SaveLayoutAction'            : 'Save current layout',
    'ClearLayoutsAction'          : 'Clear all layouts',
    'DiagnosticReportAction'      : 'Diagnostic report',
    'RunScriptAction'             : 'Run script',
    'AboutAction'                 : 'About FSLeyes',
    'PearsonCorrelateAction'      : 'Seed correlation (Pearson)',
    'ApplyFlirtXfmAction'         : 'Load affine transformation',
    'SaveFlirtXfmAction'          : 'Export affine transformation',
    'NotebookAction'              : 'Open notebooks',
    'PCACorrelateAction'          : 'Seed correlation (PCA)',
    'ResampleAction'              : 'Resample image',
    'LoadPluginAction'            : 'Load plugin',
    'ProjectImageToSurfaceAction' : 'Project image data onto surface',
    'SaveAnnotationsAction'       : 'Save annotations to file',
    'LoadAnnotationsAction'       : 'Load annotations from file',
    'EditTransformAction'         : 'Nudge',
    'CropImageAction'             : 'Crop',
    'SampleLineAction'            : 'Sample along line',
    'AddMaskDataSeriesAction'     : 'Add time series from ROI',
    'AddROIHistogramAction'       : 'Add histogram from ROI',

    'FSLeyesFrame.addOrthoPanel'           : 'Ortho View',
    'FSLeyesFrame.addLightBoxPanel'        : 'Lightbox View',
    'FSLeyesFrame.addScene3DPanel'         : '3D view',
    'FSLeyesFrame.addTimeSeriesPanel'      : 'Time series',
    'FSLeyesFrame.addHistogramPanel'       : 'Histogram',
    'FSLeyesFrame.addPowerSpectrumPanel'   : 'Power spectra',
    'FSLeyesFrame.addShellPanel'           : 'Python shell',
    'FSLeyesFrame.openHelp'                : 'Help',
    'FSLeyesFrame.setFSLDIR'               : 'Set $FSLDIR',
    'FSLeyesFrame.closeFSLeyes'            : 'Close',
    'FSLeyesFrame.selectNextOverlay'       : 'Next',
    'FSLeyesFrame.selectPreviousOverlay'   : 'Previous',
    'FSLeyesFrame.toggleOverlayVisibility' : 'Show/hide',

    'ViewPanel.removeAllPanels'             : 'Remove all panels',
    'ViewPanel.removeFromFrame'             : 'Close',

    'CanvasPanel.screenshot'                : 'Take screenshot',
    'CanvasPanel.movieGif'                  : 'Save animated GIF',
    'CanvasPanel.showCommandLineArgs'       : 'Show command line for scene',
    'CanvasPanel.applyCommandLineArgs'      : 'Apply command line arguments',
    'CanvasPanel.toggleMovieMode'           : 'Movie mode',
    'CanvasPanel.toggleDisplaySync'         : 'Link display settings',
    'CanvasPanel.toggleColourBar'           : 'Colour bar',

    'OrthoPanel.toggleEditMode'           : 'Edit mode',
    'OrthoPanel.toggleEditPanel'          : 'Edit settings panel',
    'OrthoPanel.resetDisplay'             : 'Reset display',
    'OrthoPanel.centreCursor'             : 'Centre cursor',
    'OrthoPanel.pearsonCorrelation'       : 'Seed correlation (Pearson)',
    'OrthoPanel.centreCursorWorld'        : 'Centre cursor at (0, 0, 0)',

    'OrthoPanel.toggleCursor'           : 'Show/hide location cursor',
    'OrthoPanel.toggleLabels'           : 'Show/hide labels',
    'OrthoPanel.toggleXCanvas'          : 'Show/hide X (sagittal) canvas',
    'OrthoPanel.toggleYCanvas'          : 'Show/hide Y (coronal) canvas',
    'OrthoPanel.toggleZCanvas'          : 'Show/hide Z (axial) canvas',

    'Scene3DPanel.resetDisplay'          : 'Reset camera',

    'PlotPanel.screenshot'                          : 'Take screenshot',
    'PlotPanel.importDataSeries'                    : 'Import ...',
    'PlotPanel.exportDataSeries'                    : 'Export ...',
    'OverlayPlotPanel.toggleOverlayList'            : 'Overlay list',
    'HistogramPanel.toggleHistogramOverlay'         : 'Histogram overlay',

    'OrthoViewProfile.centreCursor' : 'Centre cursor',
    'OrthoViewProfile.resetDisplay' : 'Reset display',


    'OrthoEditProfile.undo'               : 'Undo',
    'OrthoEditProfile.redo'               : 'Redo',
    'OrthoEditProfile.createMask'         : 'Create mask',
    'OrthoEditProfile.clearSelection'     : 'Clear selection',
    'OrthoEditProfile.fillSelection'      : 'Fill selection',
    'OrthoEditProfile.invertSelection'    : 'Invert selection',
    'OrthoEditProfile.eraseSelection'     : 'Erase selection',
    'OrthoEditProfile.copyPasteData'      : 'Copy/paste data',
    'OrthoEditProfile.copyPasteSelection' : 'Copy/paste 2D selection',
})


labels = TypeDict({

    'FSLeyesFrame.noOverlays'             : 'No overlays loaded',
    'FSLeyesFrame.noName'                 : '<unnamed>',
    'FSLeyesFrame.recentPathsMenu'        : 'Recent files',

    'LocationPanel.info'                      : 'Location',
    'LocationPanel.history'                   : 'History',
    'LocationInfoPanel.worldLocation'         : 'Coordinates: ',
    'LocationInfoPanel.worldLocation.unknown' : 'Unknown',
    'LocationInfoPanel.voxelLocation'         : 'Voxel location',
    'LocationInfoPanel.volume'                : 'Volume',
    'LocationInfoPanel.noData'                : 'No data',
    'LocationInfoPanel.outOfBounds'           : 'Out of bounds',
    'LocationInfoPanel.notAvailable'          : 'N/A',
    'LocationHistoryPanel.load'               : 'Load',
    'LocationHistoryPanel.save'               : 'Save',
    'LocationHistoryPanel.clear'              : 'Clear',
    'LocationHistoryPanel.hint'               :
    'Double click on an item to add a comment.',

    'OverlayListPanel.noDataSource'       : '[in memory]',

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
    'PlotControlPanel.currentDSSettings'  : 'Plot settings for {}',
    'PlotControlPanel.customDSSettings'   : 'Custom plot settings for {}',
    'PlotControlPanel.xlim'               : 'X limits',
    'PlotControlPanel.ylim'               : 'Y limits',
    'PlotControlPanel.labels'             : 'Labels',
    'PlotControlPanel.logscale'           : 'Log scale',
    'PlotControlPanel.invert'             : 'Invert',
    'PlotControlPanel.autoscale'          : 'Auto scale',
    'PlotControlPanel.scale'              : 'Axis scale',
    'PlotControlPanel.offset'             : 'Axis offset',
    'PlotControlPanel.xlabel'             : 'X',
    'PlotControlPanel.ylabel'             : 'Y',

    'TimeSeriesControlPanel.customPlotSettings' : 'Time series settings',
    'TimeSeriesControlPanel.customDSSettings'   : 'Time series settings for '
                                                  '{}',

    'PowerSpectrumControlPanel.customPlotSettings' : 'Power spectrum plot '
                                                     'settings',
    'PowerSpectrumControlPanel.customDSSettings' : 'Power spectrum '
                                                   'settings for {}',

    'HistogramControlPanel.customPlotSettings' : 'Histogram plot settings',
    'HistogramControlPanel.customDSSettings'   : 'Histogram settings for {}',

    'FEATModelFitTimeSeries.full' : 'Full model fit',
    'FEATModelFitTimeSeries.cope' : 'COPE{} fit: {}',
    'FEATModelFitTimeSeries.pe'   : 'PE{} fit',

    'FEATPartialFitTimeSeries.cope' : 'Reduced against COPE{}: {}',
    'FEATPartialFitTimeSeries.pe'   : 'Reduced against PE{}',

    'FEATResidualTimeSeries'     : 'Residuals',

    'ComplexTimeSeries'   : 'real',
    'ImaginaryTimeSeries' : 'imaginary',
    'MagnitudeTimeSeries' : 'magnitude',
    'PhaseTimeSeries'     : 'phase',

    'ComplexPowerSpectrumSeries'   : 'real',
    'ImaginaryPowerSpectrumSeries' : 'imaginary',
    'MagnitudePowerSpectrumSeries' : 'magnitude',
    'PhasePowerSpectrumSeries'     : 'phase',

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
    'OverlayDisplayPanel.VolumeRGBOpts'  : 'RGB(A) volume settings',
    'OverlayDisplayPanel.MaskOpts'       : 'Mask settings',
    'OverlayDisplayPanel.LabelOpts'      : 'Label settings',
    'OverlayDisplayPanel.RGBVectorOpts'  : 'RGB vector settings',
    'OverlayDisplayPanel.LineVectorOpts' : 'Line vector settings',
    'OverlayDisplayPanel.MeshOpts'       : 'Mesh settings',
    'OverlayDisplayPanel.TensorOpts'     : 'Diffusion tensor settings',
    'OverlayDisplayPanel.SHOpts'         : 'Diffusion SH settings',
    'OverlayDisplayPanel.MIPOpts'        : 'MIP settings',

    'OverlayDisplayPanel.3d'             : '3D display settings',

    'OverlayDisplayPanel.loadCmap'       : 'Load colour map',
    'OverlayDisplayPanel.loadVertexData' : 'Load data',
    'OverlayDisplayPanel.loadVertices'   : 'Load vertices',

    'OverlayDisplayPanel.clipPlane#'     : 'Clip plane #{}',

    'CanvasSettingsPanel.scene'    : 'Scene settings',
    'CanvasSettingsPanel.ortho'    : 'Ortho view settings',
    'CanvasSettingsPanel.lightbox' : 'Lightbox settings',
    'CanvasSettingsPanel.3d'       : '3D view settings',

    'OverlayInfoPanel.general'             : 'General information',
    'OverlayInfoPanel.overlayType'         : 'Displayed as',
    'OverlayInfoPanel.displaySpace'        : 'Display space',

    'OverlayInfoPanel.Nifti.dimensions'   : 'Dimensions',
    'OverlayInfoPanel.Nifti.transform'    : 'Transform/space',
    'OverlayInfoPanel.Nifti.orient'       : 'Orientation',
    'OverlayInfoPanel.Nifti.size'         : 'Size',

    'OverlayInfoPanel.Nifti.displaySpace.id'          : 'Raw voxels',
    'OverlayInfoPanel.Nifti.displaySpace.pixdim'      : 'True scaled voxels',
    'OverlayInfoPanel.Nifti.displaySpace.pixdim-flip' : 'Scaled voxels '
                                                        '(FSL convention)',
    'OverlayInfoPanel.Nifti.displaySpace.affine'      : 'World coordinates',
    'OverlayInfoPanel.Nifti.displaySpace.world'       : 'World coordinates',
    'OverlayInfoPanel.Nifti.displaySpace.reference'   : 'Scaled voxels '
                                                        '({}; FSL convention)',


    'OverlayInfoPanel.Analyze'                  : 'ANALYZE image',
    'OverlayInfoPanel.Image'                    : 'NIFTI image',
    'OverlayInfoPanel.Image.jsonMeta'           : 'JSON metadata',
    'OverlayInfoPanel.Image.bidsMeta'           : 'BIDS metadata',
    'OverlayInfoPanel.FEATImage'                : 'NIFTI image '
                                                  '(FEAT analysis)',
    'OverlayInfoPanel.FEATImage.featInfo'       : 'FEAT information',
    'OverlayInfoPanel.MelodicImage'             : 'NIFTI image '
                                                  '(MELODIC analysis)',
    'OverlayInfoPanel.MelodicImage.melodicInfo' : 'MELODIC information',

    'OverlayInfoPanel.Mesh'            :
    '3D mesh',
    'OverlayInfoPanel.Mesh.numVertices'            :
    'Number of vertices',
    'OverlayInfoPanel.Mesh.numTriangles'           :
    'Number of triangles',
    'OverlayInfoPanel.Mesh.displaySpace'           :
    'Display space',
    'OverlayInfoPanel.Mesh.refImage'               :
    'Reference image',
    'OverlayInfoPanel.Mesh.size'                   :
    'Size',
    'OverlayInfoPanel.Mesh.coordSpace'             :
    'Vertices defined in',
    'OverlayInfoPanel.Mesh.coordSpace.id'          :
    'Voxels ({})',
    'OverlayInfoPanel.Mesh.coordSpace.pixdim'      :
    'Scaled voxels ({})',
    'OverlayInfoPanel.Mesh.coordSpace.pixdim-flip' :
    'Scaled voxels [FSL convention] ({})',
    'OverlayInfoPanel.Mesh.coordSpace.affine'      :
    'World coordinates ({})',
    'OverlayInfoPanel.Mesh.coordSpace.display'     :
    'Display coordinate system',
    'OverlayInfoPanel.Mesh.coordSpace.torig'      :
    'Freesurfer coordinates',

    'OverlayInfoPanel.VTKMesh'        : 'VTK model',
    'OverlayInfoPanel.GiftiMesh'      : 'GIFTI surface',
    'OverlayInfoPanel.FreesurferMesh' : 'Freesurfer surface',

    'OverlayInfoPanel.dataSource'               : 'Data source',
    'OverlayInfoPanel.niftiVersion'             : 'NIFTI version',

    'OverlayInfoPanel.DTIFitTensor'             : 'DTIFit tensor images',
    'OverlayInfoPanel.DTIFitTensor.tensorInfo'  : 'Tensor image paths ',

    'OverlayInfoPanel.DicomImage'               : 'NIFTI Image (from DICOM)',
    'OverlayInfoPanel.DicomImage.dicomDir'      : 'DICOM directory',
    'OverlayInfoPanel.DicomImage.dicomMeta'     : 'DICOM metadata',

    'OverlayInfoPanel.MGHImage'                 : 'NIFTI Image (from MGH)',
    'OverlayInfoPanel.MGHImage.filename'        : 'MGH image file',

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
    'CropImagePanel.crop'             : 'Crop',
    'CropImagePanel.robustFov'        : 'Robust FOV',
    'CropImagePanel.load'             : 'Load',
    'CropImagePanel.save'             : 'Save',
    'CropImagePanel.cancel'           : 'Cancel',

    'EditTransformPanel.dsWarning'  :
    'Warning: Change the display space to "World" to see\n'
    'the effects of the transformation. You can change it\n'
    'back in the view settings panel',
    'EditTransformPanel.noOverlay'   : 'Select a NIFTI image',
    'EditTransformPanel.overlayName' : 'Transform {}',
    'EditTransformPanel.oldXform'    : 'Original transform',
    'EditTransformPanel.newXform'    : 'New transform',
    'EditTransformPanel.scale'       : 'Scale',
    'EditTransformPanel.offset'      : 'Translate',
    'EditTransformPanel.rotate'      : 'Rotate',
    'EditTransformPanel.centre'      : 'Centre of rotation',
    'EditTransformPanel.apply'       : 'Apply',
    'EditTransformPanel.reset'       : 'Reset',
    'EditTransformPanel.loadFlirt'   : 'Load affine',
    'EditTransformPanel.saveFlirt'   : 'Save affine',
    'EditTransformPanel.cancel'      : 'Close',

    'EditTransformPanel.centre.options' : {
        'volume' : 'Rotate around centre of image volume',
        'cursor' : 'Rotate around current cursor location'
    },

    'DisplaySpaceWarning.changeDS'    : 'Change display space',

    'FlirtFileDialog.load.message' :
    'Select an affine transformation matrix file',

    'FlirtFileDialog.save.message' :
    'Specify a file name for the affine transformation',

    'FlirtFileDialog.source'              : 'Source image:\n{}',
    'FlirtFileDialog.refChoiceSelectFile' : 'Select file manually',
    'FlirtFileDialog.matFile'             : 'Matrix file',
    'FlirtFileDialog.affType'             : 'File type',
    'FlirtFileDialog.affType.flirt'       : 'FLIRT',
    'FlirtFileDialog.affType.v2w'         : 'Voxel-to-world',
    'FlirtFileDialog.refImage'            : 'Reference image',
    'FlirtFileDialog.refFile'             : 'Reference image file',
    'FlirtFileDialog.selectFile'          : 'Choose',
    'FlirtFileDialog.ok'                  : 'Ok',
    'FlirtFileDialog.cancel'              : 'Cancel',
    'FlirtFileDialog.inmemory'            : 'In-memory image',

    'ResampleDialog.ok'            : 'Ok',
    'ResampleDialog.reset'         : 'Reset',
    'ResampleDialog.cancel'        : 'Cancel',
    'ResampleDialog.interpolation' : 'Interpolation',
    'ResampleDialog.origin'        : 'Origin',
    'ResampleDialog.smoothing'     : 'Smoothing',
    'ResampleDialog.allVolumes'    : 'All volumes',
    'ResampleDialog.dtype'         : 'Data type',
    'ResampleDialog.noref'         : 'None',
    'ResampleDialog.corner'        : 'Corner',
    'ResampleDialog.centre'        : 'Centre',
    'ResampleDialog.nearest'       : 'Nearest neighbour',
    'ResampleDialog.linear'        : 'Linear',
    'ResampleDialog.cubic'         : 'Cubic',
    'ResampleDialog.uchar'         : 'Unsigned char',
    'ResampleDialog.sshort'        : 'Signed short',
    'ResampleDialog.sint'          : 'Signed int',
    'ResampleDialog.float'         : 'Float',
    'ResampleDialog.double'        : 'Double',
    'ResampleDialog.reference'     : 'Resample to reference',
    'ResampleDialog.origVoxels'    : 'Old shape',
    'ResampleDialog.origPixdims'   : 'Old pixdims',
    'ResampleDialog.newVoxels'     : 'New shape',
    'ResampleDialog.newPixdims'    : 'New pixdims',

    'NewImageDialog.uchar'         : 'Unsigned char',
    'NewImageDialog.sshort'        : 'Signed short',
    'NewImageDialog.sint'          : 'Signed int',
    'NewImageDialog.float'         : 'Float',
    'NewImageDialog.double'        : 'Double',
    'NewImageDialog.ok'            : 'Ok',
    'NewImageDialog.cancel'        : 'Cancel',
    'NewImageDialog.dtype'         : 'Data type',
    'NewImageDialog.shape'         : 'Shape',
    'NewImageDialog.pixdim'        : 'Dimensions',
    'NewImageDialog.link'          : 'link with dimensions',
    'NewImageDialog.affine'        : 'Affine',

    'XNATBrowser.ok'        : 'Download',
    'XNATBrowser.cancel'    : 'Cancel',
    'XNATBrowser.choosedir' : 'Choose a download location',

    'BrowseDicomPanel.dicomdir'          : 'Directory',
    'BrowseDicomPanel.date'              : 'Date',
    'BrowseDicomPanel.patient'           : 'Patient',
    'BrowseDicomPanel.institution'       : 'Institution',
    'BrowseDicomPanel.SeriesNumber'      : 'Series',
    'BrowseDicomPanel.SeriesDescription' : 'Description',
    'BrowseDicomPanel.Matrix'            : 'Matrix',
    'BrowseDicomPanel.Load'              : 'Load',

    'BrowseDicomDialog.load'       : 'Load',
    'BrowseDicomDialog.cancel'     : 'Cancel',

    'FileTreePanel.loadDir'    : 'Load directory',
    'FileTreePanel.customTree' : 'Load tree file',
    'FileTreePanel.save'       : 'Save notes',
    'FileTreePanel.notes'      : 'Notes position',
    'FileListPanel.notes'      : 'Notes',
    'FileListPanel.present'    : '\u2713',
    'VariablePanel.value.none' : '<none>',
    'VariablePanel.value.any'  : '<any>',
    'VariablePanel.value.all'  : '<all>',

    'ProjectImageToSurfaceAction.message' :
    'Select an image to project onto the surface',

    'AnnotationPanel.colour'        : 'Colour',
    'AnnotationPanel.lineWidth'     : 'Width/size',
    'AnnotationPanel.fontSize'      : 'Font size',
    'AnnotationPanel.filled'        : 'Draw filled',
    'AnnotationPanel.border'        : 'Draw border',
    'AnnotationPanel.alpha'         : 'Opacity',
    'AnnotationPanel.honourZLimits' : 'Lock to depth',

    'AnnotationPanel.Point'          : 'Point',
    'AnnotationPanel.Line'           : 'Line',
    'AnnotationPanel.Arrow'          : 'Arrow',
    'AnnotationPanel.Rect'           : 'Rectangle',
    'AnnotationPanel.Ellipse'        : 'Ellipse',
    'AnnotationPanel.TextAnnotation' : 'Text',


    'SampleLinePanel.voxelfrom'  : 'From voxel coordinates:',
    'SampleLinePanel.voxelto'    : 'to:',
    'SampleLinePanel.worldfrom'  : 'From world coordinates:',
    'SampleLinePanel.worldto'    : 'to:',
    'SampleLinePanel.length'     : 'Length:',
    'SampleLinePanel.interp'     : 'Interpolation',
    'SampleLinePanel.resolution' : 'Resolution',
    'SampleLinePanel.normalise'  : 'Normalise',
    'SampleLinePanel.legend'     : 'Show legend',
    'SampleLinePanel.colour'     : 'Colour',
    'SampleLinePanel.lineWidth'  : 'Line width',
    'SampleLinePanel.lineStyle'  : 'Line style',

    'ExportSampledDataDialog.ok'     : 'Ok',
    'ExportSampledDataDialog.cancel' : 'Cancel',
    'ExportSampledDataDialog.series' :
    'Which line do you want to export data for?',
    'ExportSampledDataDialog.coords' :
    'Do you want to save the sample point\ncoordinates?',
})


properties = TypeDict({

    'DisplayContext.displaySpace'     : 'Display space',
    'DisplayContext.radioOrientation' : 'Display in radiological orientation',

    'CanvasPanel.syncLocation'       : 'Link location',
    'CanvasPanel.syncOverlayOrder'   : 'Link overlay order',
    'CanvasPanel.syncOverlayDisplay' : 'Link overlay display settings',
    'CanvasPanel.syncOverlayVolume'  : 'Link overlay volume settings',
    'CanvasPanel.movieMode'          : 'Movie mode',
    'CanvasPanel.movieRate'          : 'Movie update rate',
    'CanvasPanel.movieAxis'          : 'Movie axis',
    'CanvasPanel.movieSyncRefresh'   : 'Synchronise movie updates',
    'CanvasPanel.profile'            : 'Mode',

    'SceneOpts.showCursor'         : 'Show location cursor',
    'SceneOpts.cursorGap'          : 'Show gap at cursor centre',
    'SceneOpts.bgColour'           : 'Background colour',
    'SceneOpts.fgColour'           : 'Foreground colour',
    'SceneOpts.cursorColour'       : 'Location cursor colour',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.performance'        : 'Rendering performance',
    'SceneOpts.zoom'               : 'Zoom',
    'SceneOpts.highDpi'            : 'Enable high-DPI rendering',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label side',
    'SceneOpts.colourBarSize'      : 'Colour bar size',
    'SceneOpts.labelSize'          : 'Label size (points)',

    'LightBoxOpts.zax'            : 'Z axis',
    'LightBoxOpts.highlightSlice' : 'Highlight slice',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.zrange'         : 'Z range',

    'OrthoOpts.showXCanvas' : 'Show X canvas',
    'OrthoOpts.showYCanvas' : 'Show Y canvas',
    'OrthoOpts.showZCanvas' : 'Show Z canvas',
    'OrthoOpts.showLabels'  : 'Show labels',

    'OrthoOpts.layout'      : 'Layout',
    'OrthoOpts.xzoom'       : 'X zoom',
    'OrthoOpts.yzoom'       : 'Y zoom',
    'OrthoOpts.zzoom'       : 'Z zoom',

    'Scene3DOpts.showLegend'    : 'Show orientation',
    'Scene3DOpts.light'         : 'Lighting',
    'Scene3DOpts.showLight'     : 'Show light source',
    'Scene3DOpts.lightPos'      : 'Light position',
    'Scene3DOpts.lightDistance' : 'Light distance',
    'Scene3DOpts.occlusion'     : 'Volume occlusion',

    'PlotCanvas.legend'     : 'Show legend',
    'PlotCanvas.ticks'      : 'Show ticks',
    'PlotCanvas.grid'       : 'Show grid',
    'PlotCanvas.gridColour' : 'Grid colour',
    'PlotCanvas.bgColour'   : 'Background colour',
    'PlotCanvas.smooth'     : 'Smooth',
    'PlotCanvas.xAutoScale' : 'Auto-scale (x axis)',
    'PlotCanvas.yAutoScale' : 'Auto-scale (y axis)',
    'PlotCanvas.xLogScale'  : 'Log scale (x axis)',
    'PlotCanvas.yLogScale'  : 'Log scale (y axis)',
    'PlotCanvas.invertX'    : 'Invert X axis',
    'PlotCanvas.invertY'    : 'Invert Y axis',
    'PlotCanvas.xlabel'     : 'X label',
    'PlotCanvas.ylabel'     : 'Y label',

    'TimeSeriesPanel.plotMode'         : 'Plotting mode',
    'TimeSeriesPanel.usePixdim'        : 'Use pixdims',
    'TimeSeriesPanel.plotMelodicICs'   : 'Plot component time courses for '
                                         'Melodic images',
    'TimeSeriesPanel.plotFullModelFit' : 'Plot full model fit',
    'TimeSeriesPanel.plotResiduals'    : 'Plot residuals',

    'HistogramPanel.histType'    : 'Histogram type',
    'HistogramPanel.plotType'    : 'Plot type',

    'PowerSpectrumPanel.plotFrequencies' : 'Show frequencies along x axis ',
    'PowerSpectrumPanel.plotMelodicICs'  : 'Plot component power spectra for '
                                           'Melodic images',

    'DataSeries.colour'    : 'Colour',
    'DataSeries.alpha'     : 'Line transparency',
    'DataSeries.lineWidth' : 'Line width',
    'DataSeries.lineStyle' : 'Line style',

    'ComplexTimeSeries.plotReal'      : 'Plot real',
    'ComplexTimeSeries.plotImaginary' : 'Plot imaginary',
    'ComplexTimeSeries.plotMagnitude' : 'Plot magnitude',
    'ComplexTimeSeries.plotPhase'     : 'Plot phase',

    'ComplexPowerSpectrumSeries.plotReal'      : 'Plot real',
    'ComplexPowerSpectrumSeries.plotImaginary' : 'Plot imaginary',
    'ComplexPowerSpectrumSeries.plotMagnitude' : 'Plot magnitude',
    'ComplexPowerSpectrumSeries.plotPhase'     : 'Plot phase',
    'ComplexPowerSpectrumSeries.zeroOrderPhaseCorrection' :
    'Zero order phase correction (degrees)',
    'ComplexPowerSpectrumSeries.firstOrderPhaseCorrection' :
    'First order phase correction (seconds)',

    'HistogramSeries.nbins'           : 'Number of bins',
    'HistogramSeries.autoBin'         : 'Automatic histogram binning',
    'HistogramSeries.ignoreZeros'     : 'Ignore zeros',
    'HistogramSeries.includeOutliers' : 'Include values out of data range',
    'HistogramSeries.volume'          : 'Volume',
    'HistogramSeries.dataRange'       : 'Data range',
    'HistogramSeries.showOverlay'     : 'Show 3D histogram overlay',

    'ComplexHistogramSeries.plotReal'      : 'Plot real',
    'ComplexHistogramSeries.plotImaginary' : 'Plot imaginary',
    'ComplexHistogramSeries.plotMagnitude' : 'Plot magnitude',
    'ComplexHistogramSeries.plotPhase'     : 'Plot phase',

    'PowerSpectrumSeries.varNorm'     : 'Normalise to [-1, 1]',

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

    'NiftiOpts.custom_volume' : 'Volume',

    'ColourMapOpts.displayRange'     : 'Display range',
    'ColourMapOpts.clippingRange'    : 'Clipping range',
    'ColourMapOpts.modulateRange'    : 'Modulate range',
    'ColourMapOpts.linkLowRanges'    : 'Link low display/clipping ranges',
    'ColourMapOpts.linkHighRanges'   : 'Link high display/clipping ranges',
    'ColourMapOpts.modulateAlpha'    : 'Modulate alpha by intensity',
    'ColourMapOpts.cmap'             : 'Colour map',
    'ColourMapOpts.custom_cmap'      : 'Colour map',
    'ColourMapOpts.cmapResolution'   : 'Colour map resolution',
    'ColourMapOpts.gamma'            : 'Gamma correction',
    'ColourMapOpts.interpolateCmaps' : 'Interpolate colour maps',
    'ColourMapOpts.negativeCmap'     : '-ve colour map',
    'ColourMapOpts.useNegativeCmap'  : '-ve colour map',
    'ColourMapOpts.invert'           : 'Invert colour map',
    'ColourMapOpts.invertClipping'   : 'Invert clipping range',

    'VolumeOpts.clipImage'                : 'Clip by',
    'VolumeOpts.modulateImage'            : 'Modulate by',
    'VolumeOpts.interpolation'            : 'Interpolation',
    'VolumeOpts.channel'                  : 'RGB(A) channel',
    'VolumeOpts.enableOverrideDataRange'  : 'Override image data range',
    'VolumeOpts.overrideDataRange'        : 'Override image data range',
    'VolumeOpts.custom_overrideDataRange' : 'Override image data range',

    'Volume3DOpts.numSteps'                : 'Number of samples',
    'Volume3DOpts.blendFactor'             : 'Blending',
    'Volume3DOpts.blendByIntensity'        : 'Blend by intensity',
    'Volume3DOpts.smoothing'               : 'Smoothing',
    'Volume3DOpts.resolution'              : 'Quality',
    'Volume3DOpts.numClipPlanes'           : 'Number of clipping planes',
    'Volume3DOpts.showClipPlanes'          : 'Show clipping planes',
    'Volume3DOpts.clipMode'                : 'Clipping mode',
    'Volume3DOpts.clipPosition'            : 'Clip position (%)',
    'Volume3DOpts.clipInclination'         : 'Clip Z angle',
    'Volume3DOpts.clipAzimuth'             : 'Clip rotation',

    'ComplexOpts.component' : 'Component',

    'MaskOpts.colour'        : 'Colour',
    'MaskOpts.invert'        : 'Invert',
    'MaskOpts.threshold'     : 'Threshold',
    'MaskOpts.outline'       : 'Show outline only',
    'MaskOpts.outlineWidth'  : 'Outline width',
    'MaskOpts.interpolation' : 'Interpolation',

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
    'VectorOpts.modulateMode'    : 'Modulation mode',
    'VectorOpts.orientFlip'      : 'L/R orientation flip',

    'RGBVectorOpts.interpolation' : 'Interpolation',
    'RGBVectorOpts.unitLength'    : 'Scale vectors to unit length',

    'LineVectorOpts.directed'    : 'Interpret vectors as directed',
    'LineVectorOpts.lineWidth'   : 'Line width',
    'LineVectorOpts.unitLength'  : 'Scale vectors to unit length',
    'LineVectorOpts.lengthScale' : 'Length scaling factor (%)',

    'MeshOpts.colour'            : 'Colour',
    'MeshOpts.outline'           : 'Show outline only',
    'MeshOpts.outlineWidth'      : 'Outline width',
    'MeshOpts.refImage'          : 'Reference image',
    'MeshOpts.coordSpace'        : 'Mesh coordinate space',
    'MeshOpts.custom_vertexSet'  : 'Surface definition',
    'MeshOpts.custom_vertexData' : 'Vertex data',
    'MeshOpts.vertexSet'         : 'Surface definition',
    'MeshOpts.vertexData'        : 'Vertex data',
    'MeshOpts.modulateData'      : 'Modulate by',
    'MeshOpts.vertexDataIndex'   : 'Vertex data index',
    'MeshOpts.showName'          : 'Show model name',
    'MeshOpts.custom_lut'        : 'Lookup table',
    'MeshOpts.lut'               : 'Lookup table',
    'MeshOpts.discardClipped'    : 'Hide clipped areas',
    'MeshOpts.wireframe'         : 'Show as wireframe',
    'MeshOpts.lighting'          : 'Enable lighting',
    'MeshOpts.flatShading'       : 'Flat shading',

    'LabelOpts.lut'          : 'Look-up table',
    'LabelOpts.outline'      : 'Show outline only',
    'LabelOpts.outlineWidth' : 'Outline width',
    'LabelOpts.showNames'    : 'Show label names',

    'TensorOpts.lighting'          : 'Lighting effects',
    'TensorOpts.tensorResolution'  : 'Ellipsoid quality',
    'TensorOpts.tensorScale'       : 'Tensor size',

    'SHOpts.lighting'        : 'Lighting effects',
    'SHOpts.normalise'       : 'Normalise FOD sizes',
    'SHOpts.size'            : 'FOD size',
    'SHOpts.radiusThreshold' : 'Radius threshold',
    'SHOpts.shResolution'    : 'FOD quality',
    'SHOpts.shOrder'         : 'Maximum SH order',
    'SHOpts.colourMode'      : 'Colour mode',
    'SHOpts.cmap'            : 'Radius colour map',
    'SHOpts.xColour'         : 'X direction colour',
    'SHOpts.yColour'         : 'Y direction colour',
    'SHOpts.zColour'         : 'Z direction colour',

    'MIPOpts.window'         : 'MIP window length (%)',
    'MIPOpts.minimum'        : 'Minimum intensity',
    'MIPOpts.absolute'       : 'Absolute intensity',

    'VolumeRGBOpts.interpolation' : 'Interpolation',
    'VolumeRGBOpts.rColour'       : 'R colour',
    'VolumeRGBOpts.gColour'       : 'G colour',
    'VolumeRGBOpts.bColour'       : 'B colour',
    'VolumeRGBOpts.suppressR'     : 'Suppress R',
    'VolumeRGBOpts.suppressG'     : 'Suppress G',
    'VolumeRGBOpts.suppressB'     : 'Suppress B',
    'VolumeRGBOpts.suppressA'     : 'Suppress A',
    'VolumeRGBOpts.suppressMode'  : 'Suppress mode',

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
                               'fill'   : 'Bucket fill',
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
    'VectorOpts.modulateMode' : {'brightness'  : 'Brightness',
                                 'alpha'       : 'Transparency'},

    'MeshOpts.refImage.none'  : 'No reference image',

    'MeshOpts.coordSpace' : {'torig'       : 'Freesurfer coordinates',
                             'affine'      : 'World coordinates',
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
                             'reference'   : 'Reference image'},

    'VolumeOpts.interpolation' : {'none'   : 'No interpolation',
                                  'linear' : 'Linear interpolation',
                                  'spline' : 'Spline interpolation'},

    'Volume3DOpts.clipMode' : {'intersection' : 'Intersection',
                               'union'        : 'Union',
                               'complement'   : 'Complement'},

    'SHOpts.colourMode' : {'radius'    : 'Colour by radius',
                           'direction' : 'Colour by direction'},

    'ComplexOpts.component' :{ 'real'  : 'Real',
                               'imag'  : 'Imaginary',
                               'mag'   : 'Magnitude',
                               'phase' : 'Phase'},

    'Display.overlayType' : {
        'volume'         : '3D/4D volume',
        'rgb'            : '3D/4D RGB(A) volume',
        'complex'        : 'Complex volume',
        'mask'           : '3D/4D mask image',
        'mip'            : 'Max intensity projection',
        'label'          : 'Label image',
        'rgbvector'      : '3-direction vector image (RGB)',
        'linevector'     : '3-direction vector image (Line)',
        'mesh'           : '3D mesh',
        'tensor'         : 'Diffusion tensor',
        'sh'             : 'Diffusion SH',
    },

    'HistogramPanel.histType' : {'probability' : 'Probability',
                                 'count'       : 'Count'},
    'HistogramPanel.plotType' : {'centre'      : 'Bin centres',
                                 'edge'        : 'Bin edges'},

    'DataSeries.lineStyle' : {
        '-'                      : 'Solid line',
        '--'                     : 'Dashed line',
        '-.'                     : 'Dash-dot line',
        ':'                      : 'Dotted line',
        (0, (5, 7))              : 'Loose dashed line',
        (0, (1, 7))              : 'Loose dotted line',
        (0, (4, 10, 1, 10))      : 'Loose dash-dot line',
        (0, (4, 1, 1, 1, 1, 1))  : 'Dash-dot-dot line',
        (0, (4, 1, 4, 1, 1, 1))  : 'Dash-dash-dot line',
    },

    'TimeSeriesPanel.plotMode' : {'normal'        : 'Normal - no '
                                                    'scaling/offsets',
                                  'demean'        : 'Demeaned',
                                  'normalise'     : 'Normalised',
                                  'percentChange' : 'Percent changed'},

    'CopyOverlayAction.component' : {'real' : 'Real',
                                     'imag' : 'Imaginary',
                                     'R'    : 'R',
                                     'G'    : 'G',
                                     'B'    : 'B',
                                     'A'    : 'A'},

    'FileTreePanel.notes' : {'left'  : 'Left',
                             'right' : 'Right'},

    'SampleLinePanel.interp' : {0 : 'Nearest neighbour',
                                1 : 'Linear',
                                2 : 'Quadratic',
                                3 : 'Cubic'},
    'SampleLinePanel.normalise' : {'none' : 'No normalisation',
                                   'x'    : 'Normalise along X axis',
                                   'y'    : 'Normalise along Y axis',
                                   'xy'   : 'Normalise along X and Y axes'},

    'ExportSampledDataDialog.saveCoordinates' : {
        'none'  : 'Do not save coordinates',
        'voxel' : 'Save voxel coordinates',
        'world' : 'Save world coordinates',
    },
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

layouts = {
    'default'  : 'Default layout',
    'melodic'  : 'MELODIC mode',
    'feat'     : 'FEAT mode',
    'ortho'    : 'Plain orthographic',
    'lightbox' : 'Plain lightbox',
    '3d'       : 'Plain 3D',
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
    'email'      : 'paul.mccarthy@ndcn.ox.ac.uk',
    'company'    : 'FMRIB Centre, Oxford, UK',
    'version'    : 'FSLeyes version: {}',
    'glVersion'  : 'OpenGL version: {}',
    'glCompat'   : 'OpenGL compatibility: {}',
    'glRenderer' : 'OpenGL renderer: {}',
    'fslVersion' : 'FSL version: {}',
    'fslPath'    : 'FSL directory: {}',
    'software'   : textwrap.dedent(
    u"""
    FSLeyes was developed at the FMRIB Centre, Nuffield Department of Clinical Neurosciences, Oxford University, United Kingdom.

    FSLeyes is a Python application which leverages the following open-source software libraries:

     - fsleyes-props [{}] (https://git.fmrib.ox.ac.uk/fsl/fsleyes/props)
     - fsleyes-widgets [{}] (https://git.fmrib.ox.ac.uk/fsl/fsleyes/widgets)
     - fslpy [{}] (https://git.fmrib.ox.ac.uk/fsl/fslpy)
     - indexed_gzip [{}] (https://github.com/pauldmccarthy/indexed_gzip/)
     - IPython [{}] (https://ipython.org/)
     - jinja2 [{}] (http://jinja.pocoo.org)
     - Jupyter notebook [{}] (https://jupyter.org)
     - matplotlib [{}] (http://www.matplotlib.org)
     - nibabel [{}] (http://nipy.org/nibabel)
     - numpy [{}] (http://www.numpy.org)
     - pillow [{}]  (http://python-pillow.org/)
     - pyopengl [{}] (http://pyopengl.sourceforge.net)
     - pyparsing [{}] (http://pyparsing.wikispaces.com/)
     - scipy [{}] (http://www.scipy.org)
     - six [{}] (https://pythonhosted.org/six/)
     - trimesh [{}] (https://github.com/mikedh/trimesh)
     - wxpython [{}] (http://www.wxpython.org)
     - wxnatpy [{}] (https://github.com/pauldmccarthy/wxnatpy/)
     - xnatpy [{}] (https://bitbucket.org/bigr_erasmusmc/xnatpy)

    Cubic/spline interpolation routines used in FSLeyes are provided by Daniel Ruijters and Philippe Th\u00E9venaz, described at http://www.dannyruijters.nl/cubicinterpolation/.

    The GLSL parser is based on code by Nicolas P . Rougier, available at https://github.com/rougier/glsl-parser, and released under the BSD license.

    Some of the icons used in FSLeyes are derived from the Freeline icon set, by Enes Dal, available at https://www.iconfinder.com/Enesdal, and released under the Creative Commons (Attribution 3.0 Unported) license.

    DICOM to NIFTI conversion is performed with Chris Rorden's dcm2niix (https://github.com/rordenlab/dcm2niix).

    The "brain_colours" colour maps were produced and provided by Cyril Pernet
    (https://doi.org/10.1111/ejn.14430).

    FSLeyes is released under Version 2.0 of the Apache Software License. Source code for FSLeyes is available at https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes

    Copyright 2016-2019 University of Oxford, Oxford, UK.
    """).strip(),

    # This is a list of all the libraries listed
    # in the software string above - the AboutDialog
    # dynamically looks up the version number for
    # each of them, and inserts them into the above
    # string.
    'libs' : ['fsleyes_props', 'fsleyes_widgets',    'fsl.version',
              'indexed_gzip',  'IPython',            'jinja2',
              'notebook',      'matplotlib',         'nibabel',
              'numpy',         'PIL',                'OpenGL',
              'pyparsing',     'scipy',              'six',
              'trimesh',       'wx',                 'wxnat',
              'xnat'],
}
