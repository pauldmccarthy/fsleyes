/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 120

/* Model view [projection] matrices */
uniform mat4 MV;
uniform mat4 MVP;

/* Coordinates of current vertex */
attribute vec3 vertex;

/* Orientation of current vertex (see TractogramOpts.orientation). */
attribute vec3 orient;

/* Vertex coordinates passed to fragment shader. */
varying   vec3 fragVertex;

/* Vertex orientation passed to fragment shader. */
varying   vec3 fragOrient;

void main(void) {

  fragOrient  =  abs(orient);
  fragVertex  = (MV  * vec4(vertex, 1)).xyz;
  gl_Position =  MVP * vec4(vertex, 1);

}
