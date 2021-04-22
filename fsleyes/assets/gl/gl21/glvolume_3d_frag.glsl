/*
 * OpenGL fragment shader used for rendering GLVolume instances in 3D.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl
#pragma include phong_lighting.glsl
#pragma include rand.glsl

/*
 * image data texture, used for colouring.
 */
{% if textureIs2D %}
uniform sampler2D imageTexture;
{% else %}
uniform sampler3D imageTexture;
{% endif %}

/*
 * Not used in 3D rendering, but must be defined
 */
uniform sampler3D clipTexture;
uniform sampler3D modulateTexture;
uniform vec3      clipImageShape;
uniform bool      imageIsClip;
uniform bool      imageIsMod;
uniform vec3      modImageShape;
uniform bool      modulateAlpha;
uniform float     modScale;
uniform float     modOffset;


/*
 * Texture containing the colour maps.
 */
uniform sampler1D colourTexture;
uniform sampler1D negColourTexture;
uniform bool      useNegCmap;

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
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Clip voxels below/above these value. This must be specified
 * in the image texture data range. invertClip inverts the logic,
 * i.e. clip voxels that are inside the clipLow/High bounds.
 */
uniform float clipLow;
uniform float clipHigh;
uniform bool  invertClip;


/*
 * Value in the image texture data range which corresponds
 * to zero - this is used to determine whether to use the
 * regular, or the negative colour texture (if useNegCmap
 * is true).
 */
uniform float texZero;

/*
 * Clipping planes - see the is_clipped function below.
 */
uniform int  numClipPlanes;
uniform vec4 clipPlanes[5];
uniform int  clipMode;

/*
 * A vector which defines how far to move in one iteration
 * of the ray-cast loop. This is added directly to the
 * image texture coordinates, so must be between 0.0 and
 * 1.0, and must have the same direction as the camera
 * vector.
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
 * If true, colours from samples along the ray are modulated
 * according to the voxel intensity before being blended.
 * Otherwise colours are simply blended according to the
 * blendFactor.
 */
uniform bool blendByIntensity;


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
 * Apply a simple lighting model to the rendered volume.
 * Light position is specified in *image texture*
 * coordinates.
 */
uniform bool lighting;
uniform vec3 lightPos;

/*
 * Image texture coordinates.
 */
varying vec3 fragTexCoord;


/*
 * Fragment location in display coordinate system.
 */
varying vec3 fragVertex;


#pragma include glvolume_common.glsl


/*
 * Test the given texture coordinate to see if it is within a
 * region clipped by the clipping plane(s).
 *
 * - numClipPlanes: Number of active clip planes. Regions which are
 *                  clipped by *all* active clip planes are not drawn.
 *
 * - clipPlanes[5]: The clip planes, specified as plane equations in the
 *                  image texture coordinate system.
 *
 * - clipMode:      How the clipping planes are applied:
 *                    - 1 clips the intersection of all planes
 *                    - 2 clips the union of all planes
 *                    - 3 clips the complement of all planes
 */
bool is_clipped(vec3 texCoord,
                int  numClipPlanes,
                vec4 clipPlanes[5],
                int  clipMode) {

  int clipIdx;
  int activeClipPlanes = 0;

  if (numClipPlanes == 0) {
    return false;
  }

  /*
   * Count the number of active clipping
   * planes (planes for which the current
   * ray position is on thwe wrong side).
   */
  for (clipIdx = 0; clipIdx < numClipPlanes; clipIdx++) {
    if (dot(clipPlanes[clipIdx].xyz, texCoord) + clipPlanes[clipIdx].w < 0) {
      activeClipPlanes += 1;
    }
  }

  /*
   * If the current position is in the
   * intersection (1), union (2), or
   * complement (3) of all clipping
   * planes, then don't sample this
   * point, and keep casting.
   */
  if      (clipMode == 1) { if (activeClipPlanes == numClipPlanes) { return true; } }
  else if (clipMode == 2) { if (activeClipPlanes >= 1)             { return true; } }
  else if (clipMode == 3) { if (activeClipPlanes == 0)             { return true; } }
  return false;
}

/*
 * Estimate the intensity gradient at a specific location within a volume.
 * Surface normals for volume lighting are based on intensity gradients.
 */
vec3 volume_gradient(vec3      texCoord,
                     sampler3D imageTexture,
                     float     stepSize,
                     int       numClipPlanes,
                     vec4      clipPlanes[5],
                     int       clipMode) {

  vec3 xstep      = vec3(stepSize, 0, 0);
  vec3 ystep      = vec3(0, stepSize, 0);
  vec3 zstep      = vec3(0, 0, stepSize);
  vec3 xbackcoord = texCoord - xstep;
  vec3 xfwdcoord  = texCoord + xstep;
  vec3 ybackcoord = texCoord - ystep;
  vec3 yfwdcoord  = texCoord + ystep;
  vec3 zbackcoord = texCoord - zstep;
  vec3 zfwdcoord  = texCoord + zstep;

  float xback = 0;
  float xfwd  = 0;
  float yback = 0;
  float yfwd  = 0;
  float zback = 0;
  float zfwd  = 0;

  if (!is_clipped(xbackcoord, numClipPlanes, clipPlanes, clipMode)) {
    xback = texture3D(imageTexture, xbackcoord).x;
  }
  if (!is_clipped(xfwdcoord, numClipPlanes, clipPlanes, clipMode)) {
    xfwd = texture3D(imageTexture, xfwdcoord).x;
  }
  if (!is_clipped(ybackcoord, numClipPlanes, clipPlanes, clipMode)) {
    yback = texture3D(imageTexture, ybackcoord).x;
  }
  if (!is_clipped(yfwdcoord, numClipPlanes, clipPlanes, clipMode)) {
    yfwd = texture3D(imageTexture, yfwdcoord).x;
  }
  if (!is_clipped(zbackcoord, numClipPlanes, clipPlanes, clipMode)) {
    zback = texture3D(imageTexture, zbackcoord).x;
  }
  if (!is_clipped(zfwdcoord, numClipPlanes, clipPlanes, clipMode)) {
    zfwd = texture3D(imageTexture, zfwdcoord).x;
  }

  return vec3(xback - xfwd, yback - yfwd, zback - zfwd) / (2 * stepSize);
}
vec3 volume_gradient(vec3      texCoord,
                     sampler2D imageTexture,
                     float     stepSize,
                     int       numClipPlanes,
                     vec4      clipPlanes[5],
                     int       clipMode) {

  vec3 xstep      = vec3(stepSize, 0, 0);
  vec3 ystep      = vec3(0, stepSize, 0);
  vec3 xbackcoord = texCoord - xstep;
  vec3 xfwdcoord  = texCoord + xstep;
  vec3 ybackcoord = texCoord - ystep;
  vec3 yfwdcoord  = texCoord + ystep;

  float xback = 0;
  float xfwd  = 0;
  float yback = 0;
  float yfwd  = 0;

  if (!is_clipped(xbackcoord, numClipPlanes, clipPlanes, clipMode)) {
    xback = texture2D(imageTexture, xbackcoord.xy).x;
  }
  if (!is_clipped(xfwdcoord, numClipPlanes, clipPlanes, clipMode)) {
    xfwd = texture2D(imageTexture, xfwdcoord.xy).x;
  }
  if (!is_clipped(ybackcoord, numClipPlanes, clipPlanes, clipMode)) {
    yback = texture2D(imageTexture, ybackcoord.xy).x;
  }
  if (!is_clipped(yfwdcoord, numClipPlanes, clipPlanes, clipMode)) {
    yfwd = texture2D(imageTexture, yfwdcoord.xy).x;
  }

  return vec3(xback - xfwd, yback - yfwd, 0) / (2 * stepSize);
}

/*
 * Apply the Phong lighting model to the given colour, sampled from a volume.
 */
vec3 volume_lighting(vec3      texCoord,
                     sampler3D imageTexture,
                     vec3      lightPos,
                     vec3      colour,
                     int       numClipPlanes,
                     vec4      clipPlanes[5],
                     int       clipMode) {

  float stepSize = 0.01;
  vec3  normal   = volume_gradient(texCoord,
                                   imageTexture,
                                   stepSize,
                                   numClipPlanes,
                                   clipPlanes,
                                   clipMode);

  normal = normalize(gl_NormalMatrix * normal);
  return phong_lighting(texCoord, normal, lightPos, colour);
}
vec3 volume_lighting(vec3      texCoord,
                     sampler2D imageTexture,
                     vec3      lightPos,
                     vec3      colour,
                     int       numClipPlanes,
                     vec4      clipPlanes[5],
                     int       clipMode) {

  float stepSize = 0.01;
  vec3  normal   = volume_gradient(texCoord,
                                   imageTexture,
                                   stepSize,
                                   numClipPlanes,
                                   clipPlanes,
                                   clipMode);

  normal = normalize(gl_NormalMatrix * normal);
  return phong_lighting(texCoord, normal, lightPos, colour);
}


void main(void) {

    vec3  texCoord    = fragTexCoord;
    vec4  colour      = vec4(0);
    vec4  finalColour = vec4(0);
    vec4  depth       = vec4(0);
    int   nsamples    = 0;
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
    vec3 dither = rayStep * rand(gl_FragCoord.x, gl_FragCoord.y);
    texCoord    = texCoord - dither;

    /*
     * Keep going until we
     * have enough colour
     */
    while (finalColour.a < 0.95) {

      /* Shift the ray along */
      texCoord += rayStep;

      /* Finish if we've exited the volume */
      if (!textest(texCoord)) {
        break;
      }

      /* check if we're in a clipped region */
      if (is_clipped(texCoord, numClipPlanes, clipPlanes, clipMode)) {
        continue;
      }

      /*
       * Only mix the colour in if the
       * voxel was not clipped and was
       * not NaN.
       */
      if (sample_volume(texCoord, vec3(0, 0, 0), vec3(0, 0, 0), voxValue, colour)) {

        if (lighting) {
          colour.rgb = volume_lighting(texCoord,
                                       imageTexture,
                                       lightPos,
                                       colour.rgb,
                                       numClipPlanes,
                                       clipPlanes,
                                       clipMode);
        }

        /*
         * weight the sample opacity by the voxel intensity
         * (normalised w.r.t. the current display range)
         */
        if (blendByIntensity) {
          colour.a = 1 - pow(1 - clamp(voxValue, 0, 1), 1 - blendFactor);
        }
        /* Or just weight by blend factor */
        else {
          colour.a = 1 - blendFactor;
        }
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
