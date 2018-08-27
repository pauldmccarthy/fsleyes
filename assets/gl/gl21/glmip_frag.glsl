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


uniform vec3 cameraDir;
uniform vec3 rayStep;


/*
 *
 */
uniform float window;


/*
 *
 */
uniform bool useMinimum;

/*
 *
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


bool compare(float value, float maxValue) {

    bool minimum = useMinimum;

    if (useAbsolute) {
        value    = abs(value);
        maxValue = abs(maxValue);
        minimum  = false;
    }

    if (minimum) {
        if (value < maxValue) {
            return true;
        }
    }
    else if (value > maxValue) {
        return true;
    }

    return false;
}


void main(void) {

    vec3  texCoord;
    vec3  startCoord;
    vec3  endCoord;
    vec3  dither;
    bool  negCmap = false;
    float value;
    float maxValue;

    if (!textest(fragTexCoord)) {
        discard;
    }

    // jitter starting coord to
    // prevent wood grain effect
    dither     = rayStep * rand(gl_FragCoord.x, gl_FragCoord.y);
    startCoord = fragTexCoord - (cameraDir * window) / 2 - dither;
    endCoord   = fragTexCoord + (cameraDir * window) / 2 - dither;

    // TODO set to sensible values based on texture
    // value limits (is it always [0, 1]?)
    if (useMinimum) maxValue =  99999;
    else            maxValue = -99999;

    for (texCoord = startCoord;
         dot(endCoord - startCoord, endCoord - texCoord) > 0;
         texCoord += rayStep) {

        if (!textest(texCoord)) {
            continue;
        }

        /* sample the volume */
        if (useSpline) value = spline_interp(imageTexture,
                                             texCoord,
                                             imageShape,
                                             0);
        else           value = texture3D(    imageTexture, texCoord).r;

        /* Skip nan values */
        if (value != value) {
            continue;
        }

        /* if using a negative colour map, we may
         * need to invert the voxel value
          */
        if (useNegCmap && value <= texZero) {

            negCmap = true;
            value   = texZero + (texZero - value);
        }

        /* only consider in-clipping-range values */
        if ((!invertClip && (value > clipLow && value < clipHigh)) ||
            ( invertClip && (value < clipLow || value > clipHigh))) {
            if (compare(value, maxValue)) {
                maxValue = value;
            }
        }
    }

    if (maxValue == 99999 || maxValue == -99999) {
        discard;
    }

    maxValue = (img2CmapXform * vec4(maxValue, 0, 0, 1)).x;

    if (negCmap) gl_FragColor = texture1D(negCmapTexture, maxValue);
    else         gl_FragColor = texture1D(cmapTexture,    maxValue);
}
