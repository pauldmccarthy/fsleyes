/*
 * OpenGL fragment shader used for rendering 2D slices of GLVolume instances.
 * Most of the sampling logic can be found in glvolume_common.glsl.
 *
 * The following jinja2 constants can be set to configure the shader:
 *
 *  - textureIs2D: If True, the shader is configured to sample from a 2D
 *                 texture. Otherwise, a 3D texture is assumed.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

/*
 * image data texture, used for colouring.
 */

{% if textureIs2D %}
uniform sampler2D imageTexture;
{% else %}
uniform sampler3D imageTexture;
{% endif %}

/*
 * image data texture, used for clipping.
 */
uniform sampler3D clipTexture;

/*
 * image data texture, used for modulating.
 */
uniform sampler3D modulateTexture;

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
 * Shape of the image
 */
uniform vec3 imageShape;

/*
 * Shape of the image texture - for 2D images, this may
 * be different from the imageShape
 */
uniform vec3 texShape;

/*
 * Shape of the clipping image.
 */
uniform vec3 clipImageShape;

/*
 * Shape of the modulate image.
 */
uniform vec3 modImageShape;

/*
 * Flag which tells the shader whether
 * the image and clip textures are actually
 * the same - if they are, set this to true
 * to avoid an extra texture lookup.
 */
uniform bool imageIsClip;

/*
 * Flag which tells the shader whether
 * the image and modulate textures are actually
 * the same - if they are, set this to true
 * to avoid an extra texture lookup.
 */
uniform bool imageIsMod;

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
 * Scaling/offset factors to normalise modulate value with.
 * These factors should convert a modulation value read from
 * the imageTexture/modulateTexture to an alpha value.
 */
uniform float modScale;
uniform float modOffset;

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
 * Modulate the alpha of each voxel by
 * its intensity.
 */
uniform bool modulateAlpha;

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
 * Texture coordinates for modulate image.
 */
varying vec3 fragModTexCoord;

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

    if (!sample_volume(fragTexCoord,
                       fragClipTexCoord,
                       fragModTexCoord,
                       voxValue,
                       colour)) {
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
