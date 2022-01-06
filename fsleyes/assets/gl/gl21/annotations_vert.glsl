/*
 * Vertex shader for annotations.
 */
#version 120

uniform   mat4 MV;
uniform   mat4 P;
attribute vec3 vertex;

void main(void) {
  gl_Position = P * MV * vec4(vertex, 1);
}
