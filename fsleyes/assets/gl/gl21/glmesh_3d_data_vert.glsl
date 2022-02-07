/*
 * Vertex shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform   mat4 MV;
uniform   mat4 MVP;
uniform   mat3 normalmat;

attribute vec3  vertex;
attribute vec3  normal;
attribute float vertexData;
attribute float modulateData;

varying   vec3  fragVertex;
varying   vec3  fragNormal;
varying   float fragVertexData;
varying   float fragModulateData;


void main(void) {

  fragVertex       = (MV * vec4(vertex, 1)).xyz;
  fragNormal       = normalize(normalmat * normal);
  fragVertexData   = vertexData;
  fragModulateData = modulateData;
  gl_Position      = MVP * vec4(vertex, 1);
}
