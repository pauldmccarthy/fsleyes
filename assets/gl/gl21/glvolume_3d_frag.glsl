/*
 * OpenGL fragment shader used for rendering GLVolume instances in 3D.
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
 * Camera direction, normalised to unit length. FSLeyes
 * uses orthographic projection, so this is the same for
 * all fragments.
 */
uniform vec3 cameraDir;

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


#pragma include glvolume_common.glsl


int niters = 100;


void main(void) {

    vec3 texCoord     = fragTexCoord;
    vec3 clipTexCoord = fragClipTexCoord;
    vec4 colour       = vec4(0, 0, 0, 0);
    vec4 finalColour  = vec4(0, 0, 0, 0);

    bool miss;

    vec3 rayStep = cameraDir / niters;

    for (int i = 0; i < niters; i++) {

      miss = sample_volume(texCoord, clipTexCoord, colour);

      texCoord     += rayStep;
      clipTexCoord += rayStep;

      if (!miss)
        continue;

      finalColour = finalColour + (1 - finalColour.a) * colour;

      if (finalColour.a >= 0.95)
        break;
    }

    gl_FragColor = finalColour;
}
