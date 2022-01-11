/*
 * Vertex shader for the VoxelSelection annotation.
 */
#version 120

uniform    mat4  MVP;
attribute  vec3  vertex;
attribute  vec3  texCoord;
varying    vec3  fragTexCoord;

void main(void) {
  gl_Position  = MVP * vec4(vertex, 1);
  fragTexCoord = texCoord;
}
