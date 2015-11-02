#!/usr/bin/env python
#
# tooltips.py - Tooltips for FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains tooltips used throughout *FSLeyes*.

Tooltips are stored in :class:`.TypeDict` dictionariesa, broadly organised
into the following categories:

 ================== ================================================
 :data:`properties` Tooltips for ``props.HasProperties`` properties.
 :data:`actions`    Tooltips for :class:`.ActionProvider` actions.
 :data:`misc`       Tooltips for everything else.
 ================== ================================================
"""


from fsl.utils.typedict import TypeDict


properties = TypeDict({

    # DisplayContext

    'DisplayContext.displaySpace' : 'The space in which overlays are '
                                    'displayed.',

    # Overlay Display
    
    'Display.name'        : 'The name of this overlay.',
    'Display.overlayType' : 'The overlay type - how this overlay should be '
                            'displayed.',
    'Display.enabled'     : 'Show/hide this overlay.',
    'Display.alpha'       : 'The opacity of this overlay.',
    'Display.brightness'  : 'The brightness of this overlay. For volume '
                            'overlays, brightness is applied as a linear '
                            'offset to the display range.',
    'Display.contrast'    : 'The contrast of this overlay. For volume '
                            'overlay, contrast is applied as a linear '
                            'scaling factor to the display range.',

    # Overlay DisplayOpts

    'ImageOpts.volume'     : 'The volume number (for 4D images).',
    'ImageOpts.resolution' : 'Spatial display resolution, in mm.',
    'ImageOpts.transform'  : 'The affine transformation matrix to apply '
                             'to this image. You can choose to display '
                             'the image without any transformation (as if '
                             'the image voxels are 1mm isotropic); or you '
                             'can choose to scale the voxels by the pixdim '
                             'values in the NIFTI header; or you can choose '
                             'to apply the affine transformation as defined '
                             'in the NIFTI header.',

    'VolumeOpts.displayRange'    : 'Data display range - the low value '
                                   'corresponds to the low colour, and the '
                                   'high value to the high colour, in the '
                                   'selected colour map.',
     
    'VolumeOpts.clippingRange'   : 'Data clipping range - voxels with values '
                                   'outside of this range will not be '
                                   'displayed.',
    'VolumeOpts.invertClipping'  : 'Invert the clipping range, so that voxels '
                                   'inside the range are not displayed, and '
                                   'voxels outside of the range are displayed.'
                                   'This option is useful for displaying '
                                   'statistic images.',
    'VolumeOpts.cmap'            : 'The colour map to use.',
    'VolumeOpts.interpolation'   : 'Interpolate the image data for display '
                                   'purposes. You can choose no  '
                                   'interpolation (equivalent to nearest '
                                   'neighbour interpolation), linear '
                                   'interpolation, or third-order spline '
                                   '(cubic) interpolation.',
    'VolumeOpts.invert'          : 'Invert the display range, so that the low '
                                   'value corresponds to the high colour, and '
                                   'vice versa.',

    'MaskOpts.colour'    : 'The colour of this mask image.',
    'MaskOpts.invert'    : 'Invert the mask threshold range, so that values '
                           'outside of the range are shown, and values '
                           'within the range are hidden.',
    'MaskOpts.threshold' : 'The mask threshold range - values outside of '
                           'this range will not be displayed.',

    'LabelOpts.lut'          : 'The lookup table to use for this label image.',
    'LabelOpts.outline'      : 'Show the outline of each labelled region '
                               'only. If unchecked, labelled regions are '
                               'filled.',
    'LabelOpts.outlineWidth' : 'If showing label outlines, this setting '
                               'controls the outline width (as a proportion '
                               'of the image voxel size). If showing filled '
                               'regions, this setting controls the size of a '
                               'transparent border around each region. In '
                               'this situation, setting the width to 0 will '
                               'prevent the border from being shown.',
    'LabelOpts.showNames'    : 'Annotate the image display with the names of '
                               'each labelled region.',

    'VectorOpts.xColour'          : 'The colour corresponding to the X '
                                    'component of the vector - the brightness '
                                    'of the colour corresponds to the '
                                    'magnitude of the X component',
    'VectorOpts.yColour'          : 'The colour corresponding to the Y '
                                    'component of the vector - the brightness '
                                    'of the colour corresponds to the '
                                    'magnitude of the Y component.',
    'VectorOpts.zColour'          : 'The colour corresponding to the Z '
                                    'component of the vector - the brightness '
                                    'of the colour corresponds to the '
                                    'magnitude of the Z component.',
    'VectorOpts.suppressX'        : 'Ignore the X vector component when '
                                    'colouring voxels.',
    'VectorOpts.suppressY'        : 'Ignore the Y vector component when '
                                    'colouring voxels.',
    'VectorOpts.suppressZ'        : 'Ignore the Z vector component when '
                                    'colouring voxels.',
    'VectorOpts.modulate'         : 'Modulate the vector colours by another '
                                    'image. The image selected here is '
                                    'normalised to lie in the range (0, 1), '
                                    'and the magnitude of each vector is '
                                    'scaled by the corresponding modulation '
                                    'value before it is coloured. The '
                                    'modulation image must have the same '
                                    'voxel dimensions as the vector image.',
    'VectorOpts.modThreshold'     : 'Vector values which have a corresponding '
                                    'modulation value that is less than this '
                                    'threshold are not displayed. The '
                                    'threshold is a proportion of the '
                                    'modulation image data range.',
    'LineVectorOpts.lineWidth'    : 'The width of each vector line, in '
                                    'display pixels.',
    'LineVectorOpts.directed'     : 'If unchecked, the vector data is assumed '
                                    'to be undirected - the vector line at '
                                    'each voxel is scaled to have a length of '
                                    '1mm, and is centered within the voxel so '
                                    'that it passes through the voxel centre.'
                                    'If this option is checked, the vector '
                                    'data is assumed to be directed - each '
                                    'vector line begins at the voxel centre, '
                                    'and is scaled to have length 0.5mm.',
    'RGBVectorOpts.interpolation' : 'Interpolate the vector data for display '
                                    'purposes. You can choose none '
                                    '(equivalent to nearest-neighbour), '
                                    'linear, or spline interpolation.',

    'ModelOpts.colour'       : 'The colour of the model.',
    'ModelOpts.outline'      : 'If checked, only the outline of the model is '
                               'displayed. Otherwise the model is filled. ',
    'ModelOpts.outlineWidth' : 'If the model outline is being displayed, this '
                               'setting controls the outline width.',
    'ModelOpts.showName'     : 'Annotate the display wiuh the model name.',
    'ModelOpts.refImage'     : 'If this model was derived from a volumetric '
                               'image, you can choose that image as a '
                               'reference. The displayed model will then be '
                               'transformed according to the '
                               'transformation/orientation settings of the '
                               'reference.',
    'ModelOpts.coordSpace'   : 'If a reference image is selected, this '
                               'setting defines the space, relative to the '
                               'reference image, in which the model '
                               'coordinates are defined.',
    
    # SceneOpts

    'SceneOpts.showCursor'         : 'Show/hide the cursor which highlights '
                                     'the current location.',
    'SceneOpts.cursorColour'       : 'Colour of the location cursor.',
    'SceneOpts.bgColour'           : 'Canvas background colour.',
    'SceneOpts.showColourBar'      : 'If the currently selected overlay is a '
                                     'volumetric image, show a colour bar '
                                     'depicting the colour/data display '
                                     'range.',
    'SceneOpts.colourBarLocation'  : 'Where to display the colour bar.',
    'SceneOpts.colourBarLabelSide' : 'What side of the colour bar to draw the '
                                     'colour bar labels.',
    'SceneOpts.performance'        : 'Rendering performance - 1 gives the '
                                     'fastest, but at the cost of lower '
                                     'display quality, and some display '
                                     'limitations. 5 gives the best '
                                     'display quality, but may be too slow on '
                                     'some older systems.',

    'OrthoOpts.showXCanvas' : 'Show / hide the X canvas.',
    'OrthoOpts.showYCanvas' : 'Show / hide the Y canvas.',
    'OrthoOpts.showZCanvas' : 'Show / hide the Z canvas.',
    'OrthoOpts.showLabels'  : 'If the currently selected overlay is a NIFTI1 '
                              'image, show / hide anatomical orientation '
                              'labels.',
    'OrthoOpts.layout'      : 'How to lay out each of the three canvases.',
    'OrthoOpts.zoom'        : 'Zoom level for all three canvases.',

    'LightBoxOpts.zoom'           : 'Zoom level - this controls how many '
                                    'slices to display.',
    'LightBoxOpts.sliceSpacing'   : 'The spacing between adjacent slices. '
                                    'The units and range of this setting '
                                    'depend upon the currently selected '
                                    'overlay.',
    'LightBoxOpts.zrange'         : 'The start/end points of the displayed '
                                    'range of slices. The units and range '
                                    'of this setting depend upon the '
                                    'currently selected overlay.',
    'LightBoxOpts.zax'            : 'Slices along this axis will be '
                                    'displayed.',
    'LightBoxOpts.showGridLines'  : 'If checked, lines will be shown between '
                                    'each slice.',
    'LightBoxOpts.highlightSlice' : 'If checked, a box will be drawn around '
                                    'the currently selected slice.',

    # ViewPanels

    'CanvasPanel.syncLocation'       : 'If checked, the location shown on '
                                       'this panel will be linked to the '
                                       'location shown on other panels (as '
                                       'long as they also have this setting '
                                       'enabled).',
    'CanvasPanel.syncOverlayOrder'   : 'If checked, the order in which '
                                       'overlays are displayed on this '
                                       'panel will be linked to order shown '
                                       'on other panels (as long as they '
                                       'also have this setting enabled). ',
    'CanvasPanel.syncOverlayDisplay' : 'If checked, the display properties '
                                       'of all overlays shown in this panel '
                                       'linked to the display properties '
                                       'on other panels (as long as they '
                                       'also have this setting enabled). ',
    'CanvasPanel.movieMode'          : 'If checked, the volume of '
                                       'the currently selected overlay '
                                       'will automatically change at a rate '
                                       'determined by the movie rate. If you '
                                       'want several overlays to be animated, '
                                       'group them using the overlay list.',
    'CanvasPanel.movieRate'          : 'The rate at which volumes are changed '
                                       'when movie mode is enabled. Low = '
                                       'fast, and high = slow.', 

    'PlotPanel.legend'    : 'Show / hide a legend for series which have '
                            'been added to the plot.',
    'PlotPanel.autoScale' : 'If checked, the plot limits are automatically '
                            'adjusted whenever the plot contents change.',
    'PlotPanel.xLogScale' : 'If checked, a log (base 10) scale is used for '
                            'the x axis.',
    'PlotPanel.yLogScale' : 'If checked, a log (base 10) scale is used for '
                            'the y axis.',
    'PlotPanel.ticks'     : 'Show / hide axis ticks and tick labels.',
    'PlotPanel.grid'      : 'Show hide plot grid.' ,
    'PlotPanel.smooth'    : 'Smooth displayed data series (with cubic spline '
                            'interpolation).',
    'PlotPanel.xlabel'    : 'Set the x axis label.',
    'PlotPanel.ylabel'    : 'Set the y axis label.',
    'PlotPanel.limits'    : 'Manually set the x/y axis limits.',

    'TimeSeriesPanel.usePixdim'        : 'If checked, the x axis data is '
                                         'scaled by the time dimension pixdim '
                                         'value specified in the NIFTI1 '
                                         'header.',
    'TimeSeriesPanel.plotMelodicICs'   : 'If checked, the component time '
                                         'courses are plotted for Melodic '
                                         'images. If not checked, Melodic '
                                         'images are treated as regular 4D '
                                         'images.',
    'TimeSeriesPanel.showMode'         : 'Choose which time series to plot - '
                                         'you can choose to plot the time '
                                         'series for the currently selected '
                                         'overlay, the time series for all '
                                         'compatible overlays, or just those '
                                         'that have been added to the time '
                                         'series list.',
    'TimeSeriesPanel.plotMode'         : 'Plotting mode. You can choose to: '
                                         '\n  - Display the data as-is.'
                                         '\n  - Remove the temporal mean from '
                                         'the data before plotting.'
                                         '\n  - Scale the data to the range '
                                         '[-1, 1].'
                                         '\n  - Scale the data to percent '
                                         'signal-changed, relative to the '
                                         'temporal mean.',
    'TimeSeriesPanel.currentColour'    : 'Colour of the current time series.',
    'TimeSeriesPanel.currentAlpha'     : 'Opacity of the current time series.',
    'TimeSeriesPanel.currentLineWidth' : 'Line width of the current time '
                                         'series.',
    'TimeSeriesPanel.currentLineStyle' : 'Line style of the current time '
                                         'series.', 

    'HistogramPanel.autoBin'     : 'If checked, automatically calculate the '
                                   'number of bins to use in the histogram '
                                   'calculation.', 
    'HistogramPanel.showCurrent' : 'Show the histogram for the currently '
                                   'selected overlay.', 
    'HistogramPanel.histType'    : 'Show histogram data as raw counts, or '
                                   'as probabilities.',

    'PowerSpectrumPanel.plotFrequencies'  : 'If checked, the x values '
                                            'are transformed into frequency '
                                            'values.',
    'PowerSpectrumPanel.plotMelodicICs'   : 'If checked, the component power '
                                            'spectra are plotted for Melodic '
                                            'images. If not checked, Melodic '
                                            'images are treated as regular 4D '
                                            'images.',
    'PowerSpectrumPanel.showMode'         : 'Choose which power spectra to '
                                            'plot -  you can choose to plot '
                                            'the power spectrum for the '
                                            'currently selected overlay, the '
                                            'power spectra for all compatible '
                                            'overlays, or just those that '
                                            'have been added to the power '
                                            'spectra list.', 

    # DataSeries

    'DataSeries.colour'    : 'Line colour.',
    'DataSeries.alpha'     : 'Line opacity.',
    'DataSeries.label'     : 'Line label (shown in the legend).',
    'DataSeries.lineWidth' : 'Line width.',
    'DataSeries.lineStyle' : 'Line style.',

    'FEATTimeSeries.plotData'         : 'Plot the input data.',
    'FEATTimeSeries.plotFullModelFit' : 'Plot the full model fit.',
    'FEATTimeSeries.plotResiduals'    : 'Plot the residuals of the full '
                                        'model fit.', 
    'FEATTimeSeries.plotEVs'          : 'Plot the EV (explanatory variable) '
                                        'time courses.',
    'FEATTimeSeries.plotPEFits'       : 'Plot the model fit to each PE '
                                        '(parameter estimate).',
    'FEATTimeSeries.plotCOPEFits'     : 'Plot the model fit to each COPE '
                                        '(Contrast of Parameter Estimates).',
    'FEATTimeSeries.plotPartial'      : 'Plot the raw data, after regression '
                                        'against the selected PE/COPE.',

    'HistogramSeries.nbins'           : 'Number of bins to use in the '
                                        'histogram calculation (not '
                                        'applicable  if auto-binning is '
                                        'enabled).',
    'HistogramSeries.ignoreZeros'     : 'Ignore zeros in the histogram '
                                        'calculation.', 
    'HistogramSeries.showOverlay'     : 'Show a 3D mask overlay highlighting '
                                        'voxels which have been included in '
                                        'the histogram.',
    'HistogramSeries.includeOutliers' : 'Include values which are outside of '
                                        'the data range - they are added to '
                                        'the first and last bins.',
    'HistogramSeries.volume'          : 'Current volume to calculate the '
                                        'histogram for (4D images only).',
    'HistogramSeries.dataRange'       : 'Data range to include in the '
                                        'histogram.',


    'PowerSpectrumSeries.varNorm'     : 'If checked, the data is demeaned and '
                                        'normalised by its standard deviation '
                                        'before its power spectrum is '
                                        'calculated via a fourier transform.', 

    # Profiles

    'OrthoPanel.profile'                      : 'Switch between view mode '
                                                'and edit mode',
    'OrthoEditProfile.selectionSize'          : 'Size (in voxels) of the '
                                                'selection region.',
    'OrthoEditProfile.selectionIs3D'          : 'Choose between a 2D square '
                                                'selection in the plane of '
                                                'the active canvas, or a 3D '
                                                'cube.',
    'OrthoEditProfile.selectionCursorColour'  : 'Colour to use for the '
                                                'selection cursor.', 
    'OrthoEditProfile.selectionOverlayColour' : 'Colour to use to highlight '
                                                'selected regions.', 
    'OrthoEditProfile.fillValue'              : 'Value to fill the selected '
                                                'region with.' , 
    'OrthoEditProfile.intensityThres'         : 'If selecting by intensity, '
                                                'the threshold above which '
                                                'adjacent voxels are '
                                                'considered to have similar '
                                                'values for the purpose of '
                                                'the search.',
    'OrthoEditProfile.localFill'              : 'If selecting by intensity, '
                                                'only select voxels which are '
                                                'adjacent to an already  '
                                                'selected voxel',
    'OrthoEditProfile.limitToRadius'          : 'If selecting by intensity, '
                                                'limit the search to a sphere '
                                                'of the specified radius.',
    'OrthoEditProfile.searchRadius'           : 'Limit the search to the '
                                                'specified radius.',

    'OrthoEditToolBar.selint' : 'Select voxels based on similar intensities',
})


actions = TypeDict({
    'CanvasPanel.screenshot'        : 'Take a screenshot of the current scene',
    
    'OrthoToolBar.more'             : 'Show more view control settings',
    'LightBoxToolBar.more'          : 'Show more view control settings',

    'OrthoViewProfile.resetZoom'    : 'Reset zoom level to 100%',
    'OrthoViewProfile.centreCursor' : 'Reset location to centre of scene',

    'OrthoEditProfile.undo'                    : 'Undo the most recent action',
    'OrthoEditProfile.redo'                    : 'Redo the most recent '
                                                 'undone action',
    'OrthoEditProfile.fillSelection'           : 'Fill the selection with '
                                                 'the current fill value',
    'OrthoEditProfile.clearSelection'          : 'Clear the current selection',
    'OrthoEditProfile.createMaskFromSelection' : 'Create a new mask overlay '
                                                 'from the current selection',
    'OrthoEditProfile.createROIFromSelection'  : 'Create a new ROI overlay '
                                                 'from the current selection',

    'VolumeOpts.resetDisplayRange' : 'Reset the display range '
                                     'to the data range.',
    
    'OverlayDisplayToolBar.more' : 'Show more overlay display settings.',
})



misc = TypeDict({
    'PlotControlPanel.labels' : 'X/Y axis labels.',
    'PlotControlPanel.xlim'   : 'X axis data limits.',
    'PlotControlPanel.ylim'   : 'Y axis data limits.'
})
