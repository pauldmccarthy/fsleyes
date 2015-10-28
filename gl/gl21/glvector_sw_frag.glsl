/*
 * OpenGL fragment shader used for colouring GLRGBVector and GLLineVector
 * instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;

/*
 * Modulation texture containing values by
 * which the vector colours are to be modulated.
 */
uniform sampler3D modTexture;

/*
 * If the modulation value is below this
 * threshold, the fragment is made
 * transparent.
 */
uniform float modThreshold;

/*
 * Colour map for the X vector component.
 */
uniform sampler1D xColourTexture;

/*
 * Colour map for the Y vector component.
 */
uniform sampler1D yColourTexture;

/*
 * Colour map for the Z vector component.
 */
uniform sampler1D zColourTexture;

/*
 * Matrix which transforms from vector image
 * texture values to their original data range.
 */
uniform mat4 voxValXform;

/*
 * Matrix which transforms from vector image data
 * values to colour map texture coordinates.
 */
uniform mat4 cmapXform;

/*
 * Corresponding texture coordinates
 */
varying vec3 fragTexCoord;


void main(void) {

  /*
   * Look up the xyz vector values
   */
  vec3 voxValue = texture3D(imageTexture, fragTexCoord).xyz;

  /* Look up the modulation value */
  float modValue = texture3D(modTexture, fragTexCoord).x;

  /*
   * Transform the voxel texture values 
   * into a range suitable for colour texture
   * lookup, and take the absolute value
   */
  voxValue *= voxValXform[0].x;
  voxValue += voxValXform[3].x;
  voxValue  = abs(voxValue);
  voxValue *= cmapXform[0].x;
  voxValue += cmapXform[3].x;

  /* Apply the modulation value */
  voxValue *= modValue;

  /* Look up the colours for the xyz components */
  vec4 xColour = texture1D(xColourTexture, voxValue.x);
  vec4 yColour = texture1D(yColourTexture, voxValue.y);
  vec4 zColour = texture1D(zColourTexture, voxValue.z);

  /* Combine those colours */
  vec4 voxColour = xColour + yColour + zColour;

  /* Take the highest alpha of the three colour maps */
  voxColour.a = max(max(xColour.a, yColour.a), zColour.a);

  /* Knock out voxels where the modulation value is below the threshold */
  if (modValue < modThreshold)
      voxColour.a = 0.0;

  gl_FragColor = voxColour;
}
