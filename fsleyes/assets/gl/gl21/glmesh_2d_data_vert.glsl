/*
 * Vertex shader used for drawing 2D GLMesh cross sections when the vertices
 * are coloured coloured by some data.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3  vertex;
attribute float vertexData;
attribute float modulateData;
varying   float fragVertexData;
varying   float fragModulateData;

void main(void) {

  fragVertexData   = vertexData;
  fragModulateData = modulateData;
  gl_Position      = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
