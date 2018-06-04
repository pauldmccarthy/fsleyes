/*
 * This file contains the sample_volume function, shared by the different
 * glvolume fragment shaders.
 *
 * The sample_volume function looks up a specific voxel value, and applies
 * clipping and colouring.  It returns false if the fragment should be
 * discarded, otherwise it returns true.
 *
 * The voxValue output is normalised to the range [0, 1] according to the
 * current display range.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
bool sample_volume(vec3      texCoord,
                   vec3      clipTexCoord,
                   out float voxValue,
                   out vec4  finalColour) {

  float clipValue;
  bool  negCmap = false;

  /*
   * Look up the voxel value
   */
  if (useSpline) voxValue = spline_interp(imageTexture,
                                          texCoord,
                                          imageShape,
                                          0);
  else           voxValue = texture3D(    imageTexture, texCoord).r;

  /* Skip nan values */
  if (voxValue != voxValue) {
    return false;
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
                                                  clipTexCoord,
                                                  clipImageShape,
                                                  0);
  else                  clipValue = texture3D(    clipTexture,
                                                  clipTexCoord).r;

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
    return false;
  }

  /*
   * Transform the voxel value to a colour map texture
   * coordinate, and look up the colour for the voxel value
   */
  voxValue = (img2CmapXform * vec4(voxValue, 0, 0, 1)).x;

  if (negCmap) finalColour = texture1D(negColourTexture, voxValue);
  else         finalColour = texture1D(colourTexture,    voxValue);

  return true;
}
