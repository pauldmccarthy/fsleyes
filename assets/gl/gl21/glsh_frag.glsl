/*
 * OpenGL fragment shader used for rendering GLSH instances.
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


uniform sampler3D modulateTexture;
uniform sampler3D clipTexture;

uniform float clipLow;
uniform float clipHigh;

uniform float modLow;
uniform float modHigh;

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


varying vec3 fragTexCoord;

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

    gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
    return;
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

  float modValue  = texture3D(modulateTexture, fragTexCoord).x;
  float clipValue = texture3D(clipTexture,     fragTexCoord).x;

  /* Knock out voxels where the clipping value is outside the clipping range */
  if (clipValue <= clipLow || clipValue >= clipHigh) {
      gl_FragColor.a = 0.0;
      return;
  }

  /* Scale the modulation value, and modulate the colour  */
  modValue    = (modValue + modLow) / (modHigh - modLow);
  colour.xyz *= modValue; 
  

  gl_FragColor = colour * fragColourFactor;
}
