/*
 * OpenGL fragment shader used for rendering 2D slices of GLVolume instances.
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
 * image data texture, used for clipping.
 */
uniform sampler3D clipTexture;

/*
 * Texture containing the colour map.
 */
uniform sampler1D colourTexture;

/*
 * Texture containing the negative colour map.
 */
uniform sampler1D negColourTexture;

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
 * Shape of the clipping image.
 */
uniform vec3 clipImageShape;

/*
 * Flag which tells the shader whether
 * the image and clip textures are actually
 * the same - if they are, set this to true
 * to avoid an extra texture lookup.
 */
uniform bool imageIsClip;

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


/*
 * Texture coordinates for clipping image.
 */
varying vec3 fragClipTexCoord;

/*
 * Multiplicative factor to apply to the colour - can
 * be used for vertex-based lighting.
 */
varying vec4 fragColourFactor;


#pragma include glvolume_common.glsl


void main(void) {

    vec4 colour;
    float voxValue;

    /*
     * Skip voxels that are out of the image bounds
     */
    if (!test_in_bounds(fragVoxCoord, imageShape)) {
        discard;
    }

    if (!sample_volume(fragTexCoord, fragClipTexCoord, voxValue, colour)) {
        discard;
    }

    gl_FragColor = colour * fragColourFactor;

    /*
     * Set the fragment depth on a per-voxel basis
     * so that items at adjacent voxels (e.g.
     * tensors) overlap, rather than intersect.
     */
    gl_FragDepth = fragVoxCoord.x / imageShape.x *
                   fragVoxCoord.y / imageShape.y *
                   fragVoxCoord.z / imageShape.z;
}
