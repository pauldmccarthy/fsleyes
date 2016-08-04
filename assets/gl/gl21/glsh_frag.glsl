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
 * Shape of the image, used for discarding out of bounds fragments.
 */
uniform vec3 imageShape;

/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragVoxCoord;

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
  }

  else {

    vec4 normRadius = cmapXform * vec4(fragRadius, 0, 0, 1);
    
    colour = texture1D(cmapTexture, normRadius.x);
  }

  gl_FragColor = colour * fragColourFactor;
}
