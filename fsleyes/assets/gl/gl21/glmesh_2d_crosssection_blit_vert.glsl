/*
 * Vertex shader used by the GLMesh for drawing 2D cross sections.
 * Simply passes the vertex coordinates through - they are assumed
 * to be in clip space.
 */
#version 120

attribute vec3 vertex;

void main(void) {
  gl_Position  = vec4(vertex, 1);
}
