/*
 * Vertex shader used by the GLMesh for drawing 2D cross sections.
 * Simply applies the MVP to the vertex coordinates.
 */
#version 120

uniform   mat4 MVP;
attribute vec3 vertex;

void main(void) {
  gl_Position  = MVP * vec4(vertex, 1);
}
