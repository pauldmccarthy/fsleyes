/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 120

/* Model view [projection] matrices */
uniform mat4 MVP;

/* Coordinates of current vertex */
attribute vec3 vertex;

/*
 * Vertex data passed to fragment shader. The value will either
 * be the streamline orientation, or a scalar per-vertex data value,
 * depending on how the tractogram is being coloured.
 */

attribute {{ dataType }} data;
varying   {{ dataType }} fragData;

void main(void) {

  fragData    = data;
  gl_Position = MVP * vec4(vertex, 1);
}
