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
 * Number of active clip planes. Regions which are clipped
 * by *all* active clip planes are not drawn.
 */
uniform int numClipPlanes;

/*
 * The clip planes, specified as plane equations in the image
 * texture coordinate system.
 */
uniform vec4 clipPlanes[5];


/*
 * How the clipping planes are applied:
 *   -  1 clips the intersection of all planes
 *   -  2 clips the union of all planes
 *   -  3 clips the complement of all planes
 */
uniform int clipMode;

/*
 * A vector which defines how far to move in one iteration
 * of the ray-cast loop. This is added directly to the
 * image texture coordinates, so must be between 0.0 and
 * 1.0, and must have the same direction as the camera
 * vector the camera vector
 *
 * Passing in 0.0 will cause an infinite loop, and
 * passing in 1.0 will cause the loop to skip over the
 * entire texture on the first iteration, so be sensible.
 */
uniform vec3 rayStep;


/*
 * Length of the rayStep vector.
 */
uniform float stepLength;



/*
 * A constant value between 0 and 1 which controls how
 * much each sampled point contributes to the final colour.
 */
uniform float blendFactor;


/*
 * Final transparency that the fragment should have.
 */
uniform float alpha;


/*
 * A transformation matrix which transforms from image texture
 * coordinates into screen coordinates. Required to calculate
 * the final depth value for each fragment.
 */
uniform mat4 tex2ScreenXform;

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

    vec3  texCoord         = fragTexCoord;
    vec3  clipTexCoord     = fragClipTexCoord;
    vec4  colour           = vec4(0);
    vec4  finalColour      = vec4(0);
    vec4  depth            = vec4(0);
    int   nsamples         = 0;
    int   activeClipPlanes = 0;
    float voxValue;
    int   clipIdx;

    /*
     * Dither by applying a random offset
     * to the starting position. The
     * ditherDir vector must be in the
     * same direction as the cameraDir,
     * otherwise the loop below will
     * occasionally break on the first
     * iteration.
     */
    vec3 dither  = rayStep * rand(gl_FragCoord.x, gl_FragCoord.y);
    texCoord     = texCoord     - dither;
    clipTexCoord = clipTexCoord - dither;

    /*
     * Keep going until we
     * have enough colour
     */
    while (finalColour.a < 0.95) {

      /* Shift the ray along */
      texCoord     += rayStep;
      clipTexCoord += rayStep;

      /* Finish if we've exited the volume */
      if (!textest(texCoord)) {
        break;
      }

      /*
       * Count the number of active clipping
       * planes (planes for which the current
       * ray position is on thwe wrong side).
       */
      activeClipPlanes = 0;
      for (clipIdx = 0; clipIdx < numClipPlanes; clipIdx++) {
        if (dot(clipPlanes[clipIdx].xyz, texCoord) + clipPlanes[clipIdx].w < 0) {
          activeClipPlanes += 1;
        }
      }

      /*
       * If the current position is in the
       * intersection, union, or complement
       * of all clipping planes, then don't
       * sample this point, and keep casting.
       */
      if (numClipPlanes > 0) {
        if      (clipMode == 1) { if (activeClipPlanes == numClipPlanes) continue; }
        else if (clipMode == 2) { if (activeClipPlanes >= 1)             continue; }
        else if (clipMode == 3) { if (activeClipPlanes == 0)             continue; }
      }

      /*
       * Only mix the colour in if the
       * voxel was not clipped and was
       * not NaN.
       */
      if (sample_volume(texCoord, clipTexCoord, voxValue, colour)) {

        /*
         * weight the sample opacity by the voxel intensity
         * (normalised w.r.t. the current display range)
         */
        colour.a     = 1.0 - pow(1.0 - clamp(voxValue, 0, 1), blendFactor);
        colour.rgb  *= colour.a;
        finalColour += (1 - finalColour.a) * colour;
        nsamples    += 1;

        /*
         * If this is the first sample on the ray,
         * set the fragment depth to its location
         */
        if (nsamples == 1) {
          depth = tex2ScreenXform * vec4(texCoord, 1.0);
        }
      }
    }

    if (nsamples > 0) {

      finalColour.a *= alpha;
      gl_FragDepth   = depth.z;
      gl_FragColor   = finalColour;
    }
    else {
      discard;
    }
}
