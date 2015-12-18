/*
 * OpenGL fragment shader used for colouring GLRGBVector and GLLineVector
 * instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;

/*
 * Modulation texture containing values by
 * which the vector colours are to be modulated.
 */
uniform sampler3D modulateTexture;

/*
 * Texture containing values which determine
 * whether a vector voxel should be clipped.
 */
uniform sampler3D clipTexture;

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
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * If the clipping value is outside of
 * this range, the fragment is clipped.
 * These values should be in the texture 
 * data range of the clipTexture.
 */
uniform float clipLow;
uniform float clipHigh;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragVoxCoord;

/*
 * Corresponding texture coordinates
 */
varying vec3 fragTexCoord;

/*
 * The final fragment colour is multiplied by this 
 * scaling factor - this may be used for vertex-based
 * lighting.
 */
varying vec4 fragColourFactor;


void main(void) {

  vec3 voxCoords = fragVoxCoord;

  if (!test_in_bounds(voxCoords, imageShape)) {

    gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
    return;
  }

  /*
   * Look up the xyz vector values
   */
  vec3 voxValue;
  if (useSpline) {
    voxValue.x = spline_interp(imageTexture, fragTexCoord, imageShape, 0);
    voxValue.y = spline_interp(imageTexture, fragTexCoord, imageShape, 1);
    voxValue.z = spline_interp(imageTexture, fragTexCoord, imageShape, 2);
  }
  else {
    voxValue = texture3D(imageTexture, fragTexCoord).xyz;
  }

  /* Look up the modulation and clipping values */
  float modValue;
  float clipValue;
  if (useSpline) {
    modValue  = spline_interp(modulateTexture, fragTexCoord, imageShape, 0);
    clipValue = spline_interp(clipTexture,     fragTexCoord, imageShape, 0);
  }
  else {
    modValue  = texture3D(modulateTexture, fragTexCoord).x;
    clipValue = texture3D(clipTexture,     fragTexCoord).x;
  }

  /* Knock out voxels where the clipping value is outside the clipping range */
  if (clipValue < clipLow || clipValue > clipHigh) {
      gl_FragColor.a = 0.0;
      return;
  }

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

  gl_FragColor = voxColour * fragColourFactor;
}
