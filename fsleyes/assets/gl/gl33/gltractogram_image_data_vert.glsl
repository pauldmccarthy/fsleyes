/*
 * Vertex shader for rendering GLTractogram instances when being coloured
 * by data from a 3D image.
 */
#version 330

uniform mat4 MVP;

/* Coordinates of current vertex. Passed through to geometry shader. */
in  vec3 vertex;

{% for dtype in passThru %}
out {{ dtype }} geomData{{ loop.index0 }};
{% endfor %}

void main(void) {
  {% for _ in passThru %}
  geomData{{ loop.index0 }} = vertex;
  {% endfor %}
  gl_Position = MVP * vec4(vertex, 1);
}
