/*
 * Vertex shader for the VoxelSelection annotation.
 */
#version 120

uniform    mat4  MV;
uniform    mat4  P;
attribute  vec3  vertex;
attribute  vec3  texCoord;
varying    vec3  fragTexCoord;

void main(void) {
  gl_Position  = P * MV * vec4(vertex, 1);
  fragTexCoord = texCoord;
}
