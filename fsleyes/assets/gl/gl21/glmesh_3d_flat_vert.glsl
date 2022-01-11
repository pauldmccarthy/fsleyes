/*
 * Vertex shader used for drawing GLMeshes in 3D.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform   mat4 MV;
uniform   mat4 MVP;
uniform   mat3 normalmat;

attribute vec3 vertex;
attribute vec3 normal;
varying   vec3 fragVertex;
varying   vec3 fragNormal;

void main(void) {
  fragVertex   = (MV * vec4(vertex, 1)).xyz;
  fragNormal   = normalize(normalmat * normal);
  gl_Position  = MVP * vec4(vertex, 1);
}
