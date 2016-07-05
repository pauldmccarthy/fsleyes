/*
 * OpenGL fragment shader used for rendering GLCSD instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


#pragma include test_in_bounds.glsl

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragVoxCoord;

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

  gl_FragColor = vec4(1, 0, 0, 1) * fragColourFactor;;
}
