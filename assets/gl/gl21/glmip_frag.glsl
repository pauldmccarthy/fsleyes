/*
 * OpenGL fragment shader used for rendering 2D slices of GLMIP instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl


/*
 * image data texture, used for colouring.
 */
uniform sampler3D imageTexture;


/*
 * Texture containing the colour map.
 */
uniform sampler1D cmapTexture;

/*
 * Texture containing the negative colour map.
 */
uniform sampler1D negCmapTexture;

/*
 * Matrix which can be used to transform a texture value
 * from the imageTexture into a texture coordinate for
 * the colourTexture.
 */
uniform mat4 img2CmapXform;

/*
 * Shape of the imageTexture/clipTexture.
 */
uniform vec3 imageShape;

/*
 * Flag which determines whether to
 * use the negative colour map.
 */
uniform bool useNegCmap;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Clip voxels below this value. This must be specified
 * in the image texture data range.
 */
uniform float clipLow;

/*
 * Clip voxels above this value. This must be specified
 * in the image texture data range.
 */
uniform float clipHigh;

/*
 * Value in the image texture data range which corresponds
 * to zero - this is used to determine whether to use the
 * regular, or the negative colour texture (if useNegCmap
 * is true).
 */
uniform float texZero;

/*
 * Invert clipping behaviour - clip voxels
 * that are inside the clipLow/High bounds.
 */
uniform bool invertClip;

/*
 * Image voxel coordinates.
 */
varying vec3 fragVoxCoord;

/*
 * Corresponding image texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    if (!test_in_bounds(fragVoxCoord, imageShape)) {
        discard;
    }

    gl_FragColor = vec4(0, 0, 1, 0.5);
}
