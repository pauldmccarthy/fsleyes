/*
 * Vertex shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec3 normal;
uniform   vec3 lightPos;
varying   vec3 fragVertex;
varying   vec3 fragNormal;
varying   vec3 fragLightPos;

void main(void) {
  fragLightPos = (gl_ModelViewMatrix * vec4(lightPos, 1)).xyz;
  fragVertex   = (gl_ModelViewMatrix * vec4(vertex, 1)).xyz;
  fragNormal   = normalize(gl_NormalMatrix * normal);
  gl_Position  = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
