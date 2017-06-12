/*
 * OpenGL fragment shader used for rendering GLVolume instances.
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


void main(void) {

    float voxValue;
    float clipValue;
    vec4  normVoxValue;
    vec4  colour;
    bool  negCmap  = false;
    vec3  voxCoord = fragVoxCoord;

    /*
     * Skip voxels that are out of the image bounds
     */
    if (!test_in_bounds(voxCoord, imageShape)) {
        discard;
    }

    /*
     * Look up the voxel value
     */
    if (useSpline) voxValue = spline_interp(imageTexture,
                                            fragTexCoord,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture,
                                            fragTexCoord).r;

    /* Skip nan values */
    if (voxValue != voxValue) {
      discard;
    }


    /*
     * Look up the clipping value
     */

    if (imageIsClip)
      clipValue = voxValue;

    /*
     * Out of bounds of the clipping texture
     */
    else if (any(lessThan(   fragClipTexCoord, vec3(0))) ||
             any(greaterThan(fragClipTexCoord, vec3(1)))) {
      clipValue = clipLow + 0.5 * (clipHigh - clipLow);
    }

    else if (useSpline)   clipValue = spline_interp(clipTexture,
                                                    fragClipTexCoord,
                                                    clipImageShape,
                                                    0);
    else                  clipValue = texture3D(    clipTexture,
                                                    fragClipTexCoord).r;

    /*
     * If we are using a negative colour map,
     * and the voxel value is below the negative
     * threshold (texZero) invert the voxel
     * value, and set a flag telling the code
     * below to use the neagtive colour map.
     */
    if (useNegCmap && voxValue <= texZero) {

        negCmap  = true;
        voxValue = texZero + (texZero - voxValue);

        // Invert the clip value as well, if the
        // image and clip textures are the same
        if (imageIsClip) {
          clipValue = texZero + (texZero - clipValue);
        }
    }

    /*
     * Clip out of range voxel values
     */

    if ((!invertClip && (clipValue <= clipLow || clipValue >= clipHigh)) ||
        ( invertClip && (clipValue >= clipLow && clipValue <= clipHigh))) {
        discard;
    }

    /*
     * Transform the voxel value to a colour map texture
     * coordinate, and look up the colour for the voxel value
     */
    normVoxValue = img2CmapXform * vec4(voxValue, 0, 0, 1);

    if (negCmap) colour = texture1D(negColourTexture, normVoxValue.x);
    else         colour = texture1D(colourTexture,    normVoxValue.x);

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
