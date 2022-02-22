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
{% for dtype in passThru %}
in  {{ dtype }} data{{     loop.index0 }};
out {{ dtype }} geomData{{ loop.index0 }};
{% endfor %}

void main(void) {
  {% for _ in passThru %}
  geomData{{ loop.index0 }} = data{{ loop.index0 }};
  {% endfor %}
  gl_Position = MVP * vec4(vertex, 1);
}
