/*
 * Fragment shader used for drawing GLMesh instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com> 
 */
#version 120

uniform sampler1D cmap;
varying vec3      fragColour;

void main(void) {

  gl_FragColor.rgb = fragColour;
  gl_FragColor.a   = 1;
}
