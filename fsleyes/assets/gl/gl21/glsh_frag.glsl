/*
 * OpenGL fragment shader used for rendering GLSH instances,
 * when they are to be coloured by direction or radius.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


#pragma include test_in_bounds.glsl


/*
 * Colour mode:
 * 0 == colour by direction
 * 1 == colour by radius
 */
uniform int colourMode;


/*
 * Texture containing a colour map used when colouring by radius.
 */
uniform sampler1D cmapTexture;


/*
 * Texture to modulate the final colour by.
 */
uniform sampler3D modulateTexture;


/*
 * Texture to clip voxels by
 */
uniform sampler3D clipTexture;


/*
 * Clipping range, specified in the clipTexture texture data range.
 */
uniform float clipLow;
uniform float clipHigh;


/*
 * Modulation range, specified in the modulateTexture texture data range.
 */
uniform float modLow;
uniform float modHigh;

/*
 * Modulation mode:
 *   - 0 == modulate brightness by mod image
 *   - 1 == modulate alpha by mod image
 */
uniform int modulateMode;

/*
 * Scale/offset transform used to transform cmapTexture values into
 * their original data range.
 */
uniform mat4 cmapXform;


/*
 * Colours used when colouring by direction.
 */
uniform vec4 xColour;
uniform vec4 yColour;
uniform vec4 zColour;


/*
 * Scale/offset to be applied to the fragment
 * colour when colouring by direction. Encodes
 * a brightness/contrast adjustment.
 */
uniform mat4 colourXform;


/*
 * Shape of the image, used for discarding out of bounds fragments.
 */
uniform vec3 imageShape;


/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragVoxCoord;


/*
 * Corresponding vector image texture coordinates.
 */
varying vec3 fragVecTexCoord;

/*
 * Texture coordinates for clip/modulate
 * images.
 */
varying vec3 fragClipTexCoord;
varying vec3 fragModTexCoord;


/*
 * Vertex location on the FOD.
 */
varying vec3 fragVertex;


/*
 * Vertex radius.
 */
varying float fragRadius;


/*
 * The final fragment colour is multiplied by this
 * scaling factor - this may be used for vertex-based
 * lighting.
 */
varying vec4 fragColourFactor;


void main(void) {

  vec3 voxCoords = fragVoxCoord;
  vec3 normVertex;
  vec4 colour;

  if (!test_in_bounds(voxCoords, imageShape)) {
    discard;
  }

  if (colourMode == 0) {
    normVertex = abs(normalize(fragVertex));
    colour      = xColour * normVertex.x;
    colour     += yColour * normVertex.y;
    colour     += zColour * normVertex.z;

    colour.xyz *= colourXform[0].x;
    colour.xyz += colourXform[3].x;
  }

  else {

    vec4 normRadius = cmapXform * vec4(fragRadius, 0, 0, 1);
    colour = texture1D(cmapTexture, normRadius.x);
  }

  float clipValue;
  float modValue;

  /* Clobber the clip values if out of bounds */
  if (any(lessThan(   fragClipTexCoord, vec3(0))) ||
      any(greaterThan(fragClipTexCoord, vec3(1)))) {

    clipValue = clipLow + 0.5 * (clipHigh - clipLow);
  }
  else {
    clipValue = texture3D(clipTexture, fragClipTexCoord).x;

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
    modValue = texture3D(modulateTexture, fragModTexCoord).x;
  }

  /* Knock out voxels where the clipping value is outside the clipping range */
  if (clipValue <= clipLow || clipValue >= clipHigh) {
      discard;
  }

  /* Scale the modulation value, and modulate the colour or alpha  */
  modValue = (modValue + modLow) / (modHigh - modLow);

  if      (modulateMode == 0) { colour.xyz *= modValue; }
  else if (modulateMode == 1) { colour.a   *= modValue; }

  gl_FragColor = colour * fragColourFactor;
  gl_FragDepth = fragVoxCoord.x / imageShape.x *
                 fragVoxCoord.y / imageShape.y *
                 fragVoxCoord.z / imageShape.z;
}
