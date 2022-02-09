/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 120

/* Model view [projection] matrices */
uniform mat4 MVP;

/* Coordinates of current vertex */
attribute vec3 vertex;

/* Orientation of current vertex (see TractogramOpts.orientation). */
attribute vec3 orient;

/* Vertex orientation passed to fragment shader. */
varying   vec3 fragOrient;

void main(void) {

  // Orientation is used for RGB colouring.
  // We have to apply abs here in the vertex
  // shader, so that GL doesn't interpolate
  // across -ve/+ve boundaries.
  fragOrient  = abs(orient);
  gl_Position = MVP * vec4(vertex, 1);

}
