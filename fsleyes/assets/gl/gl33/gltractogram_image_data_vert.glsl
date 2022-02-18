/*
 * Vertex shader for rendering GLTractogram instances when being coloured
 * by data from a 3D image.
 */
#version 330

uniform mat4 MVP;

/* Coordinates of current vertex. Passed through to geometry shader. */
in  vec3 vertex;
out vec3 geomData;

void main(void) {
  geomData    = vertex;
  gl_Position = MVP * vec4(vertex, 1);
}
