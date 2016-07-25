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
 *
 */
uniform sampler1D cmapTexture;


uniform mat4 cmapXform;


uniform vec4 xColour;
uniform vec4 yColour;
uniform vec4 zColour;


/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragVoxCoord;

varying vec3 fragVertex;

/*
 * The final fragment colour is multiplied by this 
 * scaling factor - this may be used for vertex-based
 * lighting.
 */
varying vec4 fragColourFactor;

varying float fragRadius;


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
    colour.a    = xColour.a;
  }

  else {

    vec4 normRadius = cmapXform * vec4(fragRadius, 0, 0, 1);
    
    colour = texture1D(cmapTexture, normRadius.x);
  }

  gl_FragColor = colour * fragColourFactor;
}
