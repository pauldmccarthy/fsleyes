/*
 * Vertex shader for annotations.
 */

#version 120

uniform    mat4  MV;
uniform    mat4  P;
uniform    vec4  colour;
attribute  vec3  vertex;
varying    vec4  fragColour;

void main(void) {
  fragColour  = colour;
  gl_Position = P * MV * vec4(vertex, 1);

}
