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
uniform sampler3D vectorTexture;

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
 * Matrix which transforms from vector image
 * texture values to their original data range.
 */
uniform mat4 voxValXform;

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Colour for the X vector component.
 */
uniform vec4 xColour;

/*
 * Colour for the Y vector component.
 */
uniform vec4 yColour;

/*
 * Colour for the Z vector component.
 */
uniform vec4 zColour;

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
    voxValue.x = spline_interp(vectorTexture, fragTexCoord, imageShape, 0);
    voxValue.y = spline_interp(vectorTexture, fragTexCoord, imageShape, 1);
    voxValue.z = spline_interp(vectorTexture, fragTexCoord, imageShape, 2);
  }
  else {
    voxValue = texture3D(vectorTexture, fragTexCoord).xyz;
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
  if (clipValue <= clipLow || clipValue >= clipHigh) {
      gl_FragColor.a = 0.0;
      return;
  }

  /*
   * Transform the voxel texture 
   * values into their original 
   * range, and take the absolute 
   * value
   */
  voxValue *= voxValXform[0].x;
  voxValue += voxValXform[3].x;
  voxValue  = abs(voxValue);

  /* Combine the xyz component colours */
  vec4 voxColour = voxValue.x * xColour +
                   voxValue.y * yColour +
                   voxValue.z * zColour;

  /* 
   * Modulate the colour - multiplying the 
   * modulation value by 2 gives better results. 
   * This may become a user setting.
   */
  voxColour.xyz *= modValue * 2;

  gl_FragColor = voxColour * fragColourFactor;
}
