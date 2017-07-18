/*
 * OpenGL fragment shader used for rendering GLVolume instances in 3D.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl
#pragma include rand.glsl

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
 * The field-of-view of the image - the length
 * of each dimension in the display coordinate
 * system.
 */
uniform vec3 imageDims;

/*
 * Camera direction, normalised to unit length. FSLeyes
 * uses orthographic projection, so this is the same for
 * all fragments. Must have a length of 1.0.
 */
uniform vec3 cameraDir;

/*
 * A vector, in the same direction as cameraDir, specifying
 * the maximum amount to dither the starting position by.
 */
uniform vec3 ditherDir;

/*
 * How far through the texture coordinate space to step
 * on each iteration of the ray-casting loop. Must be
 * between 0.0 and 1.0. Passing in 0.0 will cause an
 * infinite loop, and passing in 1.0 will cause the
 * loop to skip over the entire texture on the first
 * iteration, so be sensible.
 */
uniform float stepLength;


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

void main(void) {

    vec3 texCoord     = fragTexCoord;
    vec3 clipTexCoord = fragClipTexCoord;
    vec4 colour       = vec4(0, 0, 0, 0);
    vec4 finalColour  = vec4(0, 0, 0, 0);

    bool sampled;

    /*
     * Dither by applying a random offset
     * to the starting position. The
     * ditherDir vector must be in the
     * same direction as the cameraDir,
     * otherwise the loop below will
     * occasionally break on the first
     * iteration.
     */
    vec3 dither = ditherDir * rand(gl_FragCoord.x, gl_FragCoord.y);

    /*
     * How far to move along the camera
     * direction on each iteraction.
     * This is in 3D texture coordinates.
     *
     * The ray direction needs to be
     * adjusted by the volume FOV,
     * otherwise planes which are not
     * parallel to the camera plane get
     * sheared.
     */
    vec3 rayStep = stepLength * normalize(cameraDir / imageDims);

    texCoord = texCoord + dither;
    do {

      sampled = sample_volume(texCoord, clipTexCoord, colour);

      texCoord     += rayStep;
      clipTexCoord += rayStep;

      if (!sampled)
        continue;

      finalColour.rgb = mix(finalColour.rgb, colour.rgb, finalColour.a);
      finalColour.a   = mix(0.5 * colour.a,  1.0,        finalColour.a);

    } while ((finalColour.a < 0.95) && textest(texCoord));

    gl_FragColor = finalColour;
}
