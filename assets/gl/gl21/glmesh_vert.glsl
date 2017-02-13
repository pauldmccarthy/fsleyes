/*
 * Vertex shader used for drawing GLMesh instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com> 
 */
#version 120

attribute vec3  vertex;
attribute vec3  offset;
attribute vec3  colour;

varying   vec3 fragColour;

void main(void) {

  vec3 pos    = vertex + offset;
  fragColour  = colour;
  gl_Position = gl_ModelViewProjectionMatrix * vec4(pos, 1);
}
