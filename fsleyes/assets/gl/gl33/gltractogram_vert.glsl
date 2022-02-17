/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 330

uniform mat4 MVP;

/* Coordinates of current vertex. Passed through to geometry shader. */
in vec3 vertex;

/*
 * Vertex data value - the contents depends on how the tractogram
 * is being coloured (by orientation, or by scalar data). Passed
 * through to geometry shader.
 */
in  {{ dataType }} data;
out {{ dataType }} geomData;

void main(void) {
  geomData    = data;
  gl_Position = MVP * vec4(vertex, 1);
}
