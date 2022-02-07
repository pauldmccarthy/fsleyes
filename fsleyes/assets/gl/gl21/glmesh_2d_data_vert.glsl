/*
 * Vertex shader used for drawing 2D GLMesh cross sections when the vertices
 * are coloured coloured by some data.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform   mat4  MVP;

attribute vec3  vertex;
attribute float vertexData;
attribute float modulateData;
varying   float fragVertexData;
varying   float fragModulateData;

void main(void) {

  fragVertexData   = vertexData;
  fragModulateData = modulateData;
  gl_Position      = MVP * vec4(vertex, 1);
}
