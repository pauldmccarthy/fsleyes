/*
 * Vertex shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3  vertex;
attribute vec3  normal;
attribute float vertexData;
attribute float modulateData;

varying   vec3  fragVertex;
varying   vec3  fragNormal;
varying   float fragVertexData;
varying   float fragModulateData;


void main(void) {

  fragVertex       = (gl_ModelViewMatrix * vec4(vertex, 1)).xyz;
  fragNormal       = normalize(gl_NormalMatrix * normal);
  fragVertexData   = vertexData;
  fragModulateData = modulateData;
  gl_Position      = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
