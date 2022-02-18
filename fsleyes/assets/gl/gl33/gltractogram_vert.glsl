/*
 * Vertex shader for rendering GLTractogram instances when being
 * coloured by orientation or by per-vertex data.
 */
#version 330

uniform mat4 MVP;

/* Vertex coordinates. */
in vec3 vertex;

/*
 * Vertex data value - the type/contents depends on how the tractogram
 * is being coloured (by orientation, or by per-vertex data). Passed
 * through to geometry shader.
 */
in  {{ dataType }} data;
out {{ dataType }} geomData;

void main(void) {
  geomData    = data;
  gl_Position = MVP * vec4(vertex, 1);
}
