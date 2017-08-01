/*
 * Vertex shader used for drawing 2D GLMesh cross sections when the vertices
 * are coloured coloured by some data.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3  vertex;
attribute float vertexData;
varying   float fragVertexData;

void main(void) {

  fragVertexData = vertexData;
  gl_Position    = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
