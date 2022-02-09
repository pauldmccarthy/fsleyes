/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 330

uniform mat4 MVP;

/* Coordinates of current vertex. Passed through to geometry shader. */
in vec3 vertex;

/* Orientation of current vertex (see TractogramOpts.orientation).
 * Passed through to geometry shader.
 */
in  vec3 orient;
out vec3 geomOrient;

void main(void) {

  // Orientation is used for RGB colouring.
  // We have to apply abs here in the vertex
  // shader, so that GL doesn't interpolate
  // across -ve/+ve boundaries.
  geomOrient  = abs(orient);
  gl_Position = MVP * vec4(vertex, 1);
}
