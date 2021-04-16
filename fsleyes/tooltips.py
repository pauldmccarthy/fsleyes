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

The :func:`initTooltips` function initialises some parameters controlling
tooltip display. It is called by the :class:`.FSLeyesFrame` upon creation.
"""


from fsleyes_widgets.utils.typedict import TypeDict


def initTooltips():
    """Sets some parameters controlling tooltip display. """
    import wx
    wx.ToolTip.Enable(     True)
    wx.ToolTip.SetDelay(   1500)
    wx.ToolTip.SetMaxWidth(300)
    wx.ToolTip.SetReshow(  3000)
    wx.ToolTip.SetAutoPop( 5000)


properties = TypeDict({

    # DisplayContext

    'DisplayContext.displaySpace'     : 'The space in which overlays are '
                                        'displayed.',
    'DisplayContext.radioOrientation' : 'If checked, images oriented to the '
                                        'MNI152 standard will be displayed in '
                                        'radiological orientation (i.e. with '
                                        'subject left to the right of the '
                                        'display, and subject right to the '
                                        'left). Otherwise they will be '
                                        'displayed in neurological '
                                        'orientation (i.e. with subject left '
                                        'to the left of the display).',

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

    'NiftiOpts.volume'     : 'The volume number (for 4D images).',
    'NiftiOpts.transform'  : 'The affine transformation matrix to apply '
                             'to this image. You can choose to display '
                             'the image without any transformation (as if '
                             'the image voxels are 1mm isotropic); or you '
                             'can choose to scale the voxels by the pixdim '
                             'values in the NIFTI header; or you can choose '
                             'to apply the affine transformation as defined '
                             'in the NIFTI header.',


    'ColourMapOpts.displayRange' :
    'Data display range - the low value corresponds to the low colour, and '
    'the high value to the high colour, in the selected colour map.',

    'ColourMapOpts.clippingRange' :
    'Data clipping range - voxels with values outside of this range will not '
    'be displayed.',

    'ColourMapOpts.modulateRange' :
    'Modulation range - controls the data range used to modulate transparency',

    'ColourMapOpts.invertClipping' :
    'Invert the clipping range, so that voxels inside the range are not '
    'displayed, and voxels outside of the range are displayed. '
    'This option is useful for displaying statistic images.',

    'ColourMapOpts.cmap'            : 'The colour map to use.',
    'ColourMapOpts.custom_cmap'     : 'The colour map to use.',

    'ColourMapOpts.negativeCmap' :
    'The colour map to use for negative values.',

    'ColourMapOpts.useNegativeCmap' :
    'Enable the negative colour map - this allows positive and negative '
    'values to be coloured independently.',

    'ColourMapOpts.cmapResolution'  :
    'Colour map resolution - the number of colours to use in the colour maps.',

    'ColourMapOpts.interpolateCmaps' :
    'Interpolate between discrete colours in the colour map. If not selected, '
    'nearest-neighbour interpolation is used. ',

    'ColourMapOpts.invert' :
    'Invert the display range, so that the low value corresponds to the high '
    'colour, and vice versa.',

    'ColourMapOpts.modulateAlpha' :
    'Modulate alpha (opacity) by the intensity at each region. Regions with a '
    'value near to the low display range will have opacity near 0, and '
    'regions with a value near to the high display range will have opacity '
    'near 1.',

    'VolumeOpts.interpolation' :
    'Interpolate the image data on the display. You can choose no  '
    'interpolation (equivalent to nearest neighbour interpolation), linear '
    'interpolation, or third-order spline (cubic) interpolation.',

    'VolumeOpts.enableOverrideDataRange' :
    'Override the actual data range of an image with a user-specified '
    'one. This is useful for images which have a very large data '
    'range that is driven by outliers.',

    'VolumeOpts.overrideDataRange' :
    'Override the actual data range of an image with a user-specified '
    'one. This is useful for images which have a very large data '
    'range that is driven by outliers.',

    'VolumeOpts.custom_overrideDataRange' :
    'Override the actual data range of an image with a user-specified '
    'one. This is useful for images which have a very large data '
    'range that is driven by outliers.',

    'VolumeOpts.clipImage' :
    'Clip this image by the values contained in another image. When active, '
    'The clipping range is set according to the values in the clip image '
    'instead of in this image.',

    'VolumeOpts.modulateImage' :
    'Modulate alpha/opacity by the values contained in another image, instead '
    'of modulating by the values in this image.',

    'Volume3DOpts.numSteps' :
    'The maximum number of times that the image is sampled for each pixel.',

    'Volume3DOpts.blendFactor' :
    'This setting controls the sampling depth - a higher value will result '
    'in the final volume colour being blended from samples which are deeper '
    'in the volume.',

    'Volume3DOpts.blendByIntensity' :
    'When active, the amount by which each sample is blended into the final '
    'colour will be weighted by the voxel intensity. When inactive, samples '
    'will be blended solely according to the blending setting.',

    'Volume3DOpts.smoothing' :
    'This setting controls the amount of smoothing applied to the volume. '
    'When the smoothing is greater than zero, a gaussian smoothing filter is '
    'applied, with the filter radius (in pixels) controlled by this setting.',

    'Volume3DOpts.resolution' :
    'This setting controls the quality (resolution) at which the volume is '
    'shown on screen. Higher values look better, but lower values will be '
    'drawn more quickly.',

    'Volume3DOpts.numClipPlanes' :
    'Number of active clipping planes. Areas of the image which are in the '
    'intersection, union, or complement of all clipping planes will not be '
    'shown. The clip mode controls how clipping is applied',

    'Volume3DOpts.clipMode' :
    'How the clipping planes are applied. You can choose to clip (hide) the '
    'intersection, union, or complement of all active clipping planes',

    'Volume3DOpts.showClipPlanes' :
    'When enabled, each active clipping plane is shown.',

    'Volume3DOpts.clipPosition' :
    'Clip plane position, as a percentage of the image length.',

    'Volume3DOpts.clipInclination' :
    'Amount by which to rotate the clip plane about the X axis.',

    'Volume3DOpts.clipAzimuth' :
    'Amount by which to rotate the clip plane about the Z axis.',

    'ComplexOpts.component' :
    'Choose to display either the real or imaginary components, or the '
    'magnitude or phase.',

    'MaskOpts.colour' :
    'The colour of this mask image.',
    'MaskOpts.invert' :
    'Invert the mask threshold range, so that values outside of the range '
    'are shown, and values within the range are hidden.',
    'MaskOpts.threshold' :
    'The mask threshold range - values outside of this range will not be '
    'displayed.',
    'MaskOpts.outline' :
    'When selected, an outline of the mask is shown, instead of the filled '
    'mask being shown.',
    'MaskOpts.outlineWidth'  :
    'When the mask outline is shown, this setting controls the outline width '
    'in pixels.',
    'MaskOpts.interpolation' :
    'Interpolate the mask data on the display. You can choose no  '
    'interpolation (equivalent to nearest neighbour interpolation), linear '
    'interpolation, or third-order spline (cubic) interpolation.',

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
                                    'magnitude of the X component. This '
                                    'option has no effect if a colour image '
                                    'is selected.',
    'VectorOpts.yColour'          : 'The colour corresponding to the Y '
                                    'component of the vector - the brightness '
                                    'of the colour corresponds to the '
                                    'magnitude of the Y component. This '
                                    'option has no effect if a colour image '
                                    'is selected.',
    'VectorOpts.zColour'          : 'The colour corresponding to the Z '
                                    'component of the vector - the brightness '
                                    'of the colour corresponds to the '
                                    'magnitude of the Z component. This '
                                    'option has no effect if a colour image '
                                    'is selected.',
    'VectorOpts.suppressX'        : 'Ignore the X vector component when '
                                    'colouring voxels. This option has no '
                                    'effect if a colour image is selected.',
    'VectorOpts.suppressY'        : 'Ignore the Y vector component when '
                                    'colouring voxels. This option has no '
                                    'effect if a colour image is selected.',
    'VectorOpts.suppressZ'        : 'Ignore the Z vector component when '
                                    'colouring voxels. This option has no '
                                    'effect if a colour image is selected.',
    'VectorOpts.suppressMode'     : 'When a vector direction is suppressed,'
                                    'it\'s contribution to the resulting '
                                    'will be replaced according to this '
                                    'setting.',
    'VectorOpts.modulateImage'    : 'Modulate the vector colour brightness by '
                                    'another image. The image selected here '
                                    'is normalised to lie in the range (0, '
                                    '1), and the brightness of each vector '
                                    'colour is scaled by the corresponding '
                                    'modulation value before it is coloured. '
                                    'The modulation image must have the same '
                                    'voxel dimensions as the vector image.',
    'VectorOpts.clipImage'        : 'Clip vector voxels according to the '
                                    'values in another image. Vector voxels '
                                    'which correspond to values in the '
                                    'clipping image that have a value less '
                                    'than the current clipping threshold are '
                                    'not shown. The clipping image must have '
                                    'the same voxel dimensions as the vector '
                                    'image. ',
    'VectorOpts.colourImage'      : 'Colour the vectors according to the '
                                    'values in another image, and by the '
                                    'selected colour map. The colour image '
                                    'must have the same voxel dimensions as '
                                    'the vector image. ',
    'VectorOpts.clippingRange'    : 'Vector values which have a corresponding '
                                    'clipping image value that is outside of '
                                    'this range are not displayed. ',
    'VectorOpts.modulateRange'    : 'The data range that is used when '
                                    'modulating vector brightness by a '
                                    'modulation image.',
    'VectorOpts.modulateMode'     : 'Either the brightness, or the '
                                    'transparency, of vector voxels can be '
                                    'modulated by the modulation image.',
    'VectorOpts.cmap'             : 'Colour map to use for colouring vector '
                                    'voxels, if a colour image is selected.',
    'VectorOpts.orientFlip'       : 'If checked, direction orientations '
                                    'within each voxel are flipped about '
                                    'the x axis.',
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
    'LineVectorOpts.unitLength'   : 'If checked, the vector lines are scaled '
                                    'so that they have a length of 1mm (times'
                                    'the length scaling factor). '
                                    'Otherwise the vector lengths are '
                                    'unmodified.',
    'LineVectorOpts.lengthScale'  : 'Scale the vector line length by this '
                                    'scaling factor (expressed as a '
                                    'percentage).',
    'RGBVectorOpts.interpolation' : 'Interpolate the vector data for display '
                                    'purposes. You can choose none '
                                    '(equivalent to nearest-neighbour), '
                                    'linear, or spline interpolation.',
    'RGBVectorOpts.unitLength'    : 'If checked, the data is scaled so that '
                                    'each vector has length 1.',


    'MeshOpts.colour' :
    'The colour of the mesh, when not colouring by vertex data.',
    'MeshOpts.outline' :
    'If checked, only the outline of the mesh is displayed. Otherwise the '
    'mesh cross-section is shown. ',
    'MeshOpts.outlineWidth' :
    'If the mesh outline is being displayed, this setting controls the '
    'outline width.',
    'MeshOpts.showName' :
    'Annotate the display wiuh the model name.',
    'MeshOpts.refImage' :
    'If this model was derived from a volumetric image, you can choose that '
    'image as a reference. The displayed model will then be transformed '
    'according to the transformation/orientation settings of the reference.',
    'MeshOpts.coordSpace'   :
    'If a reference image is selected, this setting defines the space, '
    'relative to the reference image, in which the model coordinates are '
    'defined.',
    'MeshOpts.vertexSet' :
    'Choose a file which contains a surface definition (vertices) for this '
    'mesh',
    'MeshOpts.custom_vertexSet' :
    'Choose a file which contains a surface definition (vertices) for this '
    'mesh',
    'MeshOpts.vertexData' :
    'Choose a file which contains data for each vertex - you can colour the '
    'mesh outline according to the values in the file. This only applies '
    'when the mesh outline, and not its cross-section is displayed.',
    'MeshOpts.modulateData' :
    'Choose a vertex data file to modulate transparency by. If left unset, '
    'transparency is modulated by the currently selected vertex data.',
    'MeshOpts.custom_vertexData'   :
    'Choose a file which contains data for each vertex - you can colour the '
    'mesh outline according to the values in the file. This only applies '
    'when the mesh outline, and not its cross-section is displayed.',
    'MeshOpts.vertexDataIndex' :
    'If you have loaded vertex data with multiple data points for each '
    'vertex, this control allows you to control the data point that is '
    'displayed.',
    'MeshOpts.useLut' :
    'When selected, a lookup table, instead of the colour maps, is used to '
    'colour the mesh according to its vertex data. This is useful for '
    'discrete label data',
    'MeshOpts.lut' :
    'The lookup table to use when colouring the mesh with a lookup table '
    'instead of with the colour maps.',
    'MeshOpts.custom_lut' :
    'The lookup table to use when colouring the mesh with a lookup table '
    'instead of with the colour maps.',
    'MeshOpts.discardClipped' :
    'When the mesh is coloured according to some data, this setting allows '
    'you to choose between hiding the areas with data outside of the clipping '
    'range, or colouring those areas with a constant colour.',
    'MeshOpts.wireframe' :
    'When selected, the mesh is shown as a wireframe, rather than being '
    'filled.',
    'MeshOpts.lighting' :
    'When selected, a lighting effect is applied to the mesh.',
    'MeshOpts.flatShading' :
    'When selected, interpolation of the colours between adjacent vertices'
    'is not performed - each triangle in the mesh is coloured according to '
    'its first triangle.',

    'TensorOpts.lighting'         : 'If enabled, a simple lighting model is '
                                    'used to highlight the tensor '
                                    'orientations.',
    'TensorOpts.tensorResolution' : 'This setting controls the number of '
                                    'vertices used to render each tensor. '
                                    'A higher value will result in better '
                                    'looking tensors, but may reduce '
                                    'performance.' ,
    'TensorOpts.tensorScale'      : 'By default, the tensor radii are scaled '
                                    'the largest eigenvalue of the tensor '
                                    'matrix, so that the largest tensor is '
                                    'drawn to fit within a voxel. This '
                                    'setting allows the tensor scale to be '
                                    'adjusted.',

    'SHOpts.lighting'         : 'If enabled, a simple lighting model is used '
                                'to highlight the FODs',
    'SHOpts.normalise'        : 'If enabled, the size of each FOD is '
                                'normalised to fit within a voxel.',
    'SHOpts.size'             : 'This setting allows the FOD size to be '
                                'scaled up or down',
    'SHOpts.radiusThreshold'  : 'This setting allows FODs with small radius '
                                'to be hidden.',
    'SHOpts.shResolution'     : 'This setting controls the display resolution '
                                '(number of vertices) used to draw each FOD.',
    'SHOpts.shOrder'          : 'This setting controls the maximum spherical '
                                'harmonic function order with which to '
                                'display FODs.',
    'SHOpts.colourMode'       : 'FODs can be coloured according to their '
                                'radius/size, or according to their '
                                'orientation/direction. This setting is '
                                'disabled when you choose to colour the FODs '
                                'by another image (e.g. a FA map).',

    # MIPOpts
    'MIPOpts.window'  :
    'Length of the window, as a proportion of the image length, along which '
    'the MIP is calculated. The window is centred at the current display '
    'location.',
    'MIPOpts.minimum' :
    'Use the minimum intensity, rather than the maximum intensity, in the '
    'projection.',
    'MIPOpts.absolute' :
    'Use the absolute intensity, rather than the maximum intensity, in the '
    'projection. This overrides the minimum intensity setting.',
    'MIPOpts.interpolation' :
    'Interpolate the MIP data on the display. You can choose no  '
    'interpolation (equivalent to nearest neighbour interpolation), linear '
    'interpolation, or third-order spline (cubic) interpolation.',

    # SceneOpts
    'SceneOpts.showCursor'         : 'Show/hide the cursor which highlights '
                                     'the current location.',
    'SceneOpts.cursorGap'          : 'Show a gap at the cursor centre.',
    'SceneOpts.cursorColour'       : 'Colour of the location cursor.',
    'SceneOpts.bgColour'           : 'Canvas background colour.',
    'SceneOpts.fgColour' :
    'Foreground colour, used for labels and the colour bar. Note that the '
    'foreground colour will be automatically adjusted whenever you change '
    'the canvas background colour.',

    'SceneOpts.showColourBar'      : 'If the currently selected overlay is a '
                                     'volumetric image, show a colour bar '
                                     'depicting the colour/data display '
                                     'range.',
    'SceneOpts.colourBarLocation'  : 'Where to display the colour bar.',
    'SceneOpts.colourBarLabelSide' : 'What side of the colour bar to draw the '
                                     'colour bar labels.',
    'SceneOpts.colourBarSize'      : 'Size of the major axis of the colour '
                                     'bar, as a proportion of the available '
                                     'space.',
    'SceneOpts.performance'        : 'Rendering performance - 1 gives the '
                                     'fastest, but at the cost of lower '
                                     'display quality, and some display '
                                     'limitations. 3 gives the best '
                                     'display quality, but may be too slow on '
                                     'some older systems.',
    'SceneOpts.highDpi' :
    'If you are using a high-DPI (e.g. retina) display, FSLeyes will attempt '
    'to display the scene at the high-DPI resolution. This will have an '
    'effect on performance.',

    'SceneOpts.labelSize'   : 'Scale the label font size.',


    'OrthoOpts.showXCanvas' : 'Show / hide the X canvas '
                              '(sagittal in MNI space).',
    'OrthoOpts.showYCanvas' : 'Show / hide the Y canvas '
                              '(coronal in MNI space).',
    'OrthoOpts.showZCanvas' : 'Show / hide the Z canvas '
                              '(axial in MNI space).',
    'OrthoOpts.showCursor'  : 'Show/hide the location cross-hairs.',
    'OrthoOpts.showLabels'  : 'If the currently selected overlay is a NIFTI '
                              'image, show / hide anatomical orientation '
                              'labels.',
    'OrthoOpts.layout'      : 'How to lay out each of the three canvases.',
    'OrthoOpts.zoom'        : 'Zoom level for all three canvases.',

    'OrthoToolBar.showCursorAndLabels' :
    'Show/hide the location cursor and anatomical labels',

    'Scene3DToolBar.showCursorAndLegend' :
    'Show/hide the location cursor and anatomical legend',

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

    'Scene3DOpts.showLegend' :
    'When selected, a legend will be displayed in the bottom right, showing '
    'orientation information.',
    'Scene3DOpts.light'      :
    'Enable a simple lighting effect.',
    'Scene3DOpts.showLight' :
    'Show the position of the light source.',
    'Scene3DOpts.lightPos' :
    'Position of the light in the display coordinate system.',
    'Scene3DOpts.lightDistance' :
    'Distance of the light from the display centre.',
    'Scene3DOpts.occlusion' :
    'When selected, volumes in the scene which are behind another volume will '
    'not be shown. ',

    'Scene3DOpts.zoom' :
    'Zoom level - distance from the camera to the model space.',

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
                                       'are linked to the display properties '
                                       'on other panels (as long as they '
                                       'also have this setting enabled). ',
    'CanvasPanel.syncOverlayVolume'  : 'If checked,  properties which control '
                                       'the displayed volume/timepoint '
                                       'of all overlays shown in this panel '
                                       'are linked to the volume properties '
                                       'on other panels (as long as they '
                                       'also have this setting enabled). ',

    'CanvasPanel.movieMode' :
    'If checked, the volume will automatically change at a rate determined '
    'by the movie rate.  You can also loop through the or X, Y, or Z voxel '
    'coordinates by changing the movie axis  inthe view settings panel.  If '
    'you are looping through volumes and you want several overlays to be '
    'animated, group them using the overlay list.',

    'CanvasPanel.movieRate' :
    'The rate at which volumes are changed when movie mode is enabled. Low = '
    'fast, and high = slow.',

    'CanvasPanel.movieAxis' :
    'The axis to loop through. You can choose to run a movie through any '
    'axis of an image (X, Y, Z, or volume/time).',

    'CanvasPanel.movieSyncRefresh' :
    'In movie mode, refresh all orthographic canvases in a synchronous '
    'manner. This is not possible under certain platforms/environments, '
    'where the canvas updates cannot be synchronised.',

    'PlotCanvas.legend'     : 'Show / hide a legend for series which have '
                             'been added to the plot.',
    'PlotCanvas.xAutoScale' : 'If checked, the plot X axis limits are '
                             'automatically adjusted whenever the plot '
                             'contents change.',
    'PlotCanvas.yAutoScale' : 'If checked, the plot Y axis limits are '
                             'automatically adjusted whenever the plot '
                             'contents change.',
    'PlotCanvas.xLogScale'  : 'If checked, a log (base 10) scale is used for '
                             'the x axis.',
    'PlotCanvas.yLogScale'  : 'If checked, a log (base 10) scale is used for '
                             'the y axis.',
    'PlotCanvas.invertX'    : 'Invert the plot along the X axis.',
    'PlotCanvas.invertY'    : 'Invert the plot along the Y axis.',
    'PlotCanvas.ticks'      : 'Show / hide axis ticks and tick labels.',
    'PlotCanvas.grid'       : 'Show hide plot grid.' ,
    'PlotCanvas.gridColour' : 'Set the plot grid colour.' ,
    'PlotCanvas.bgColour'   : 'Set the plot background colour.' ,
    'PlotCanvas.smooth'     : 'Smooth displayed data series (with cubic spline '
                             'interpolation).',
    'PlotCanvas.xlabel'     : 'Set the x axis label.',
    'PlotCanvas.ylabel'     : 'Set the y axis label.',
    'PlotCanvas.limits'     : 'Manually set the x/y axis limits.',

    'TimeSeriesPanel.usePixdim'        : 'If checked, the x axis data is '
                                         'scaled by the time dimension pixdim '
                                         'value specified in the NIFTI '
                                         'header.',
    'TimeSeriesPanel.plotMelodicICs'   : 'If checked, the component time '
                                         'courses are plotted for Melodic '
                                         'images. If not checked, Melodic '
                                         'images are treated as regular 4D '
                                         'images.',
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

    'HistogramPanel.histType' :
    'Show histogram data as raw counts, or as probabilities.',
    'HistogramPanel.plotType'    :
    'Use histogram bin edges or bin centres for the histogram plot.',

    'PowerSpectrumPanel.plotFrequencies'  : 'If checked, the x values '
                                            'are transformed into frequency '
                                            'values.',
    'PowerSpectrumPanel.plotMelodicICs'   : 'If checked, the component power '
                                            'spectra are plotted for Melodic '
                                            'images. If not checked, Melodic '
                                            'images are treated as regular 4D '
                                            'images.',

    # DataSeries

    'DataSeries.enabled'   : 'Show/hide the line.',
    'DataSeries.colour'    : 'Line colour.',
    'DataSeries.alpha'     : 'Line opacity.',
    'DataSeries.label'     : 'Line label (shown in the legend).',
    'DataSeries.lineWidth' : 'Line width.',
    'DataSeries.lineStyle' : 'Line style.',

    'ComplexTimeSeries.plotReal' :
    'Plot the real component of a complex image.',
    'ComplexTimeSeries.plotImaginary' :
    'Plot the imaginary component of a complex image.',
    'ComplexTimeSeries.plotMagnitude' :
    'Plot the magnitude of a complex image.',
    'ComplexTimeSeries.plotPhase' :
    'Plot the phase of a complex image.',

    'ComplexPowerSpectrumSeries.plotReal' :
    'Plot the real component of the power spectrum of a complex image.',
    'ComplexPowerSpectrumSeries.plotImaginary' :
    'Plot the imaginary component of the power spectrum of a complex image.',
    'ComplexPowerSpectrumSeries.plotMagnitude' :
    'Plot the magnitude of the power spectrum of a complex image.',
    'ComplexPowerSpectrumSeries.plotPhase' :
    'Plot the phase of the power spectrum of a complex image.',
    'ComplexPowerSpectrumSeries.zeroOrderPhaseCorrection' :
    'Zero order phase correction',
    'ComplexPowerSpectrumSeries.firstOrderPhaseCorrection' :
    'First order phase correction',

    'ComplexHistogramSeries.plotReal' :
    'Plot the histogram of the real component of a complex image.',
    'ComplexHistogramSeries.plotImaginary' :
    'Plot the histogram of the imaginary component of a complex image.',
    'ComplexHistogramSeries.plotMagnitude' :
    'Plot the histogram of the magnitude of a complex image.',
    'ComplexHistogramSeries.plotPhase' :
    'Plot the histogram of the phase of a complex image.',

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

    'HistogramSeries.autoBin'         : 'If checked, automatically calculate '
                                        'the number of bins to use in the '
                                        'histogram calculation.',
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


    'PowerSpectrumSeries.varNorm' :
    'If checked, the fourier-transformed data is normalised to the range '
    '[-1, 1]. Complex valued data are normalised with respect to the '
    'absolute value. ',

    # Profiles
    'OrthoPanel.profile' :
    'Switch between view mode and edit mode',

    'OrthoEditProfile.selectionCursorColour'  :
    'Colour to use for the selection cursor.',

    'OrthoEditProfile.selectionOverlayColour' :
    'Colour to use to highlight selected regions.',

    'OrthoEditProfile.locationFollowsMouse' :
    'Change the cursor location when you click and drag to draw, erase, or '
    'select voxels. If you are using a slower computer you may wish to '
    'disable this option.',

    'OrthoEditProfile.showSelection' :
    'Show/hide the current selection, when in select mode.',

    'OrthoEditProfile.drawMode' :
    'Toggle between "draw" mode and "select" mode. In draw mode, you can '
    'simply \'draw\' on an image - when you release the mouse, the voxel '
    'values are replaced with the current fill value (or erased). Select '
    'mode is more powerful, but requires two steps to edit an image - '
    'you must first select some voxels, and then fill/erase them.',

    'OrthoEditProfile.mode' :
    'Switch between editing tools. The "Navigate" tool simply allows you to '
    'view the image and change the display location. The "Pencil" tool allows '
    'you to fill voxel values (in draw mode), or to manually select voxels '
    '(in select mode). The "Erase" tool allows you to erase voxel values (in '
    'draw mode), or to deselect voxels (in select mode). When select mode is '
    'enabled, the "select by intensity" tool allows you to select voxels '
    'based on their intensity. Click on a "seed" voxel, and all voxels with '
    'a similar intenstiy to that seed voxel will be selected.',

    'OrthoEditProfile.selectionSize' :
    'Size (in voxels) of the selection region when using the pencil or '
    'eraser tools.',

    'OrthoEditProfile.selectionIs3D' :
    'When using the pencil or eraser tools, choose between a 2D square '
    'selection in the plane of the active canvas, or a 3D cuboid. With '
    'the select by intensity tool, you can limit the selection search to '
    'the current 2D slice, or extend the search to the full 3D image.',

    'OrthoEditProfile.fillValue' :
    'Value to replace voxels with when drawing/filling.',

    'OrthoEditProfile.eraseValue' :
    'Value to replace voxels with when erasing.' ,

    'OrthoEditProfile.intensityThres' :
    'When using the select by intensity tool, this is the threshold used to '
    'determine whether or not a voxel should be selected. If the difference '
    'in intensity between the seed voxel and another voxel in the search '
    'space is less than or equal to this threshold, the voxel will be '
    'selected.',

    'OrthoEditProfile.intensityThresLimit' :
    'Upper limit for the intensity threshold. By default the upper intensity '
    'threshold limit is calculated from he image data range, but you can '
    'manually adjust it through this setting.',

    'OrthoEditProfile.localFill' :
    'When using the select by intensity tool, this setting will cause the '
    'search space to be limited to voxels which have a similar intensity '
    'to the seed voxel, and which are adjacent to another selected voxel.',

    'OrthoEditProfile.limitToRadius' :
    'When using the select by intensity tool, this setting will cause the '
    'search limited to a circle or sphere of the specified radius.',

    'OrthoEditProfile.searchRadius' :
    'When using the select by intensity tool, if the search is being limited '
    'to a radius, this setting allows you to specify the radius of the search '
    'circle/sphere.',

    'OrthoEditProfile.targetImage' : \
    'Choose the target image for edit operations. By default, when you '
    'fill/erase voxels, the currently selected image is modified. However, '
    'you can select a different image (of the same dimensions and resolution '
    'as the currently selected image) as the target for edit operations. This '
    'is most useful when selecting voxels by intensity - you can select voxels'
    'based on the values in the currently selected image, but then fill/erase '
    'that selection in another image.',
})


actions = TypeDict({
    'CanvasPanel.screenshot'        : 'Take a screenshot of the current scene',
    'CanvasPanel.OverlayDisplayPanel' : 'Show more overlay display settings',
    'CanvasPanel.CanvasSettingsPanel' : 'Show more view control settings',
    'CanvasPanel.OverlayInfoPanel'    : 'Show/hide the overlay '
                                        'information panel.',

    'OrthoPanel.toggleEditPanel' : 'Show/hide the edit settings panel',

    'PlotPanel.screenshot'       : 'Take a screenshot of the current plot.',
    'PlotPanel.importDataSeries' : 'Import data series from a text file.',
    'PlotPanel.exportDataSeries' : 'Export data series to a text file.',
    'PlotPanel.addDataSeries'    : 'Add (hold) data series '
                                   'from the current overlay.',
    'PlotPanel.removeDataSeries' : 'Remove the most recently '
                                   'added data series.',

    'TimeSeriesPanel.TimeSeriesControlPanel'  : 'Show/hide the time '
                                                'series control panel.',
    'TimeSeriesPanel.PlotListPanel'           : 'Show/hide the time '
                                                'series list panel.',
    'HistogramPanel.HistogramControlPanel'    : 'Show/hide the histogram '
                                                'control panel.',
    'HistogramPanel.PlotListPanel'            : 'Show/hide the histogram '
                                                'list panel.',

    'PowerSpectrumPanel.PowerSpectrumControlPanel'  : 'Show/hide the power '
                                                      'spectrum control '
                                                      'panel.',
    'PowerSpectrumPanel.PlotListPanel'              : 'Show/hide the power '
                                                      'spectrum list '
                                                      'panel.',

    'OrthoViewProfile.resetDisplay' : 'Reset the display on all canvases.',
    'OrthoViewProfile.centreCursor' : 'Reset location to centre of scene',

    'OrthoEditProfile.undo' :
    'Undo the most recent action. A history of changes to the selection, '
    'and to image data, are maintained. separate undo/redo histories are '
    'maintained for each image.',

    'OrthoEditProfile.redo' :
    'Redo the most recent undone action.',

    'OrthoEditProfile.createMask' :
    'Create an empty 3D mask image which has the same dimensions as the '
    'currently selected image.',

    'OrthoEditProfile.clearSelection' :
    'Clear the current selection - no voxels are selected.',

    'OrthoEditProfile.fillSelection' :
    'Fill selected voxels in the currently selected '
    'image with the current fill value. ',

    'OrthoEditProfile.eraseSelection' :
    'Set the value at all selected voxels in the currently selected '
    'image to zero.',

    'OrthoEditProfile.copyPasteData' :
    'Copy/paste data between images. Select some voxels in one image, and '
    'click this button to copy the voxel values to a clipboard. Then select '
    'another image (which has the same dimensions/resolution as the first '
    'image), and click this button again to paste the values. Shift+click the '
    'button to clear the clipboard.',

    'OrthoEditProfile.copyPasteSelection' :
    'Copy/paste 2D selections between slices. Draw a selection on one slice, '
    'and push this button to copy the selection from that slice. Then move .'
    'the cursor to a different slice, and push this button again to paste the '
    'selection into the new slice. Shift+click the button to clear the '
    'clipboard.',

    'Scene3DViewProfile.resetDisplay' :
    'Reset the zoom, pan, and rotation',

    # Items in the OverlayListPanel
    'ListItemWidget.save'  : 'Save this overlay to a file',
    'ListItemWidget.group' : 'Link some properties of this overlay '
                             'with other linked overlays (e.g. '
                             'volume)',

    'SampleLinePanel.screenshot' : 'Save the plot to a file',
    'SampleLinePanel.addDataSeries'    :
    'Add (hold) the most recently drawn data series.',
    'SampleLinePanel.removeDataSeries' :
    'Remove the most recently added data series.',

    'AnnotationPanel.loadAnnotations' :
    'Load annotations from a file',
    'AnnotationPanel.saveAnnotations' :
    'Save the currently displayed annotations to a file',
})


misc = TypeDict({
    'PlotControlPanel.labels' : 'X/Y axis labels.',
    'PlotControlPanel.logscale' :
    'If checked, a log (base 10) scale is used for the X/Y axis.',
    'PlotControlPanel.autoscale' :
    'If checked, the plot X/Y axis limits are automatically adjusted whenever '
    'the plot contents change.',
    'PlotControlPanel.invert' :
    'If checked, the plot is inverted along the X/Y axis.',
    'PlotControlPanel.scale' :
    'A constant scaling factor to apply to the data.',
    'PlotControlPanel.offset' :
    'A constant offset to apply to the data.',

    'PlotControlPanel.xlim'   : 'X axis data limits.',
    'PlotControlPanel.ylim'   : 'Y axis data limits.',

    'ResampleDialog.reference' :
    'Resample the image to the same dimensions as this reference.',
    'ResampleDialog.interpolation' :
    'The interpolation approach to use when resampling.',
    'ResampleDialog.origin' :
    'The origin common to the original space and the resampled space - .'
    'either the centre of the corner voxel, or the corner of the corner '
    'voxel.',
    'ResampleDialog.dtype' :
    'The data type of the resampled image. If you are resampling and '
    'interpolating an image with an integer data type, you may need to select '
    'a floating point type for the interpolation to have any effect.',
    'ResampleDialog.smoothing' :
    'If selected, the image data is smoothed with a gaussian filter before '
    'being resampled. This is to ensure that the values of the voxels in the '
    'image contribute more evenly to the values in the resampled image '
    'voxels. This setting has no effect when using nearest neighbour '
    'interpolation, and is only applied along axes which are being '
    'down-sampled.',
    'ResampleDialog.allVolumes' :
    'For images with more than three dimensions, this checkbox controls '
    'whether all volumes are resampled, or just the currently selected '
    'volume.',
})
