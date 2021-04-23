/*
 * OpenGL fragment shader used for rendering 2D slices of GLMIP instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl
#pragma include rand.glsl


/*
 * image data texture.
 */
uniform sampler3D imageTexture;


/*
 * Texture containing the colour map.
 */
uniform sampler1D cmapTexture;


/*
 * Minimum value in the image texture.
 */
uniform float textureMin;


/*
 * Maximum value in the image texture.
 */
uniform float textureMax;


/*
 * Matrix which can be used to transform a texture value
 * from the imageTexture into a texture coordinate for
 * the cmapTexture.
 */
uniform mat4 img2CmapXform;

/*
 * Shape of the imageTexture.
 */
uniform vec3 imageShape;


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
/*
 * Invert clipping behaviour - clip voxels
 * that are inside the clipLow/High bounds.
 */
uniform bool invertClip;


/*
 * Camera direction vector, normalised to unit length.
 */
uniform vec3 cameraDir;


/*
 * Ray cast vector - the ray is shifted by this much on each
 * iteration of the loop.
 */
uniform vec3 rayStep;


/*
 * Proportion of image (between 0 and 1) to sample from.
 */
uniform float window;


/*
 * Perform a minimum intensity projection, rather than maximum.
 */
uniform bool useMinimum;


/*
 * Perform an absolute-maximum intensity projection - overrides
 * the useMinimum flag.
 */
uniform bool useAbsolute;


/*
 * Image voxel coordinates.
 */
varying vec3 fragVoxCoord;


/*
 * Corresponding image texture coordinates.
 */
varying vec3 fragTexCoord;


/*
 * Sample the volume at the given texCoord, returning true if
 * the sampled value should be used as the new maximum.
 */
bool sample_volume(vec3 texCoord, float maxValue, out float value) {

    bool usemin = useMinimum;

    /* sample the volume */
    if (useSpline)
        value = spline_interp(imageTexture, texCoord, imageShape, 0);
    else
        value = texture3D(    imageTexture, texCoord).r;

    /* Skip nan values */
    if (value != value) {
        return false;
    }

    /* only consider in-clipping-range values */
    if ((!invertClip && (value <= clipLow || value >= clipHigh)) ||
        ( invertClip && (value >= clipLow && value <= clipHigh))) {
        return false;
    }

    /*
     * figure out if we should replace the
     * current max value with this value
     */
    if (useAbsolute) {
        value  = abs(value);
        usemin = false;
    }

    if (usemin && (value < maxValue)) {
      return true;
    }
    else if ((!usemin) && (value > maxValue)) {
        return true;
    }

    return false;
}


void main(void) {

    vec3  texCoord;
    vec3  startCoord;
    vec3  endCoord;
    vec3  dither;
    float value;
    float maxValue;

    if (!test_in_bounds(fragVoxCoord, imageShape)) {
        discard;
    }

    /*
     * Figure out the start and
     * end sampling locations
     * based on the current window.
     *
     * randomly offset starting coord
     * to prevent wood grain effect.
     */
    dither     = rayStep * rand(gl_FragCoord.x, gl_FragCoord.y);
    startCoord = fragTexCoord - (cameraDir * window) / 2 - dither;
    endCoord   = fragTexCoord + (cameraDir * window) / 2 - dither;

    /*
     * initialise max value to something
     * that we won't encounter in the
     * image data
     */
    if (useMinimum) maxValue = textureMax + 1;
    else            maxValue = textureMin - 1;

    /*
     * Sample the volume along a ray,
     * stopping when we have gone past
     * the end texture coordinates
     */
    for (texCoord = startCoord;
         dot(endCoord - startCoord, endCoord - texCoord) > 0;
         texCoord += rayStep) {

        if (!textest(texCoord)) {
            continue;
        }

        if (sample_volume(texCoord, maxValue, value)) {
            maxValue = value;
        }
    }

    /* No voxels were sampled */
    if (maxValue > textureMax || maxValue < textureMin) {
        discard;
    }

    /*
     * Turn the mip voxel value into
     * an appropriate colour
     */
    maxValue = (img2CmapXform * vec4(maxValue, 0, 0, 1)).x;
    gl_FragColor = texture1D(cmapTexture, maxValue);
}
