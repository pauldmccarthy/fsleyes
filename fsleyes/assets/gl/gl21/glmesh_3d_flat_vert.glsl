/*
 * Vertex shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform   mat4 mvmat;
uniform   mat4 mvpmat;
uniform   mat3 normalmat;

attribute vec3 vertex;
attribute vec3 normal;
varying   vec3 fragVertex;
varying   vec3 fragNormal;

void main(void) {
  fragVertex   = (mvmat * vec4(vertex, 1)).xyz;
  fragNormal   = normalize(normalmat * normal);
  gl_Position  = mvpmat * vec4(vertex, 1);
}
