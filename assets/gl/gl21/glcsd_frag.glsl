/*
 * OpenGL fragment shader used for rendering GLCSD instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


#pragma include test_in_bounds.glsl

/*
 * Colour mode:
 * 0 == colour by direction
 * 1 == colour by radius
 * 2 == use a constant colour
 */
uniform int colourMode;

/*
 *
 */
uniform sampler1D cmapTexture;


uniform mat4 cmapXform;


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
  vec4 colour;

  if (!test_in_bounds(voxCoords, imageShape)) {

    gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
    return;
  }

  if (colourMode == 1) {

    vec4 normRadius = cmapXform * vec4(fragRadius, 0, 0, 1);
    
    colour = texture1D(cmapTexture, normRadius.x);
  }

  gl_FragColor = colour * fragColourFactor;
}
