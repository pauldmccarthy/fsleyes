/*
 * Vertex shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3  vertex;
attribute vec3  normal;
varying   vec3  fragVertex;
varying   vec3  fragNormal;

void main(void) {

  fragVertex  = (gl_ModelViewMatrix * vec4(vertex, 1)).xyz;
  fragNormal  = normalize(gl_NormalMatrix * normal);
  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
