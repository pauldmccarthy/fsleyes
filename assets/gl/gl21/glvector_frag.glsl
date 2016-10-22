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


/* Shapes of the modulate/clipping images */
uniform vec3 modImageShape;
uniform vec3 clipImageShape;

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
 * Scale/offset transformation matrix 
 * which scales the voxel value before 
 * it is combined with the direction 
 * colours. Used to apply brightness
 * and contrast settings.
 */
uniform mat4 colourXform;

/*
 * If the clipping value is outside of
 * this range, the fragment is clipped.
 * These values should be in the texture 
 * data range of the clipTexture.
 */
uniform float clipLow;
uniform float clipHigh;

/*  
 * The modulation value is scaled to this 
 * range before being applied.
 */
uniform float modLow;
uniform float modHigh;

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
varying vec3 fragVecTexCoord;

/*
 * Texture coordinates for the clipping 
 * and modulate images.
 */
varying vec3 fragClipTexCoord;
varying vec3 fragModTexCoord;

/*
 * The final fragment colour is multiplied by this 
 * scaling factor - this may be used for vertex-based
 * lighting.
 */
varying vec4 fragColourFactor;


void main(void) {

  vec3 voxCoords = fragVoxCoord;

  if (!test_in_bounds(voxCoords, imageShape)) {
    discard;
  }

  /*
   * Look up the xyz vector values
   */
  vec3 voxValue;
  if (useSpline) {
    voxValue.x = spline_interp(vectorTexture, fragVecTexCoord, imageShape, 0);
    voxValue.y = spline_interp(vectorTexture, fragVecTexCoord, imageShape, 1);
    voxValue.z = spline_interp(vectorTexture, fragVecTexCoord, imageShape, 2);
  }
  else {
    voxValue = texture3D(vectorTexture, fragVecTexCoord).xyz;
  }

  /* Look up the modulation and clipping values */
  float modValue;
  float clipValue;

  /* Clobber the clip values if out of bounds */
  if (any(lessThan(   fragClipTexCoord, vec3(0))) ||
      any(greaterThan(fragClipTexCoord, vec3(1)))) {
    
    clipValue = clipLow + 0.5 * (clipHigh - clipLow);
  }
  
  else {
    if (useSpline) {
      clipValue = spline_interp(clipTexture, fragClipTexCoord, clipImageShape, 0);
    }
    else {
      clipValue = texture3D(clipTexture, fragClipTexCoord).x;
    }
  }

  /* And do the same for the modulation value */
  if (any(lessThan(   fragModTexCoord, vec3(0))) ||
      any(greaterThan(fragModTexCoord, vec3(1)))) {

    /* 
     * modValue gets scaled by the mod range down 
     * below, but if we give it this value, the 
     * scaling step will result in a value of 1
     */
    modValue = modHigh - 2 * modLow;
  }
  
  else {
    if (useSpline) {
      modValue = spline_interp(modulateTexture, fragModTexCoord, modImageShape,  0);
    }
    else {
      modValue = texture3D(modulateTexture, fragModTexCoord).x;
    } 
  }

  /* Knock out voxels where the clipping value is outside the clipping range */
  if (clipValue <= clipLow || clipValue >= clipHigh) {
      discard;
  }

  /*
   * Transform the voxel texture 
   * values into their original 
   * range, and take the absolute 
   * value.
   */
  voxValue *= voxValXform[0].x;
  voxValue += voxValXform[3].x;
  voxValue  = abs(voxValue);

  /* Combine the xyz component colours. */
  vec4 voxColour = voxValue.x * xColour +
                   voxValue.y * yColour +
                   voxValue.z * zColour;

  /* 
   * Apply the colour scale/offset -
   * this affects overall brightness,
   * and contrast between the three 
   * colours.
   */
  voxColour.xyz *= colourXform[0].x;
  voxColour.xyz += colourXform[3].x; 

  /* 
   * Scale the modulation value, and 
   * modulate the colour (but not alpha).
   */
  modValue       = (modValue + modLow) / (modHigh - modLow);
  voxColour.xyz *= modValue;

  gl_FragColor = voxColour * fragColourFactor;
  gl_FragDepth = fragVoxCoord.x / imageShape.x *
                 fragVoxCoord.y / imageShape.y *
                 fragVoxCoord.z / imageShape.z;
}
