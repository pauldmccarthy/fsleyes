/*
 * Vertex shader used by the GLMesh for drawing 2D cross sections.
 * Calculates the intersection of the mesh with a clipping plane.
 */
#version 120


uniform   vec4  clipPlane;
uniform   mat4  MVP;
attribute vec3  vertex;
varying   float clipDistance;

void main(void) {
  clipDistance = dot(clipPlane.xyz, vertex.xyz) + clipPlane.w;
  gl_Position  = MVP * vec4(vertex, 1);
}
