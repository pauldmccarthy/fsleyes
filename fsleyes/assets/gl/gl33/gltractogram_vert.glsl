/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 330

uniform mat4 MVP;

/* Vertex coordinates. */
in vec3 vertex;

/*
 * Vertex data value - the type/contents depends on how the tractogram
 * is being coloured (by orientation, by per-vertex data, or by image data).
 * Passed through to geometry shader.
 */
{% if colourMode == 'orientation' %}
in  vec3 orient;
out vec3 geomOrient;
{% elif colourMode == 'vertexData' %}
in  float vertexData;
out float geomVertexData;
{% elif colourMode == 'imageData' %}
out vec3 geomVertex;
{% endif %}

{% if clipMode == 'vertexData' %}
in  float clipVertexData;
out float geomClipVertexData;
{% endif %}


void main(void) {

  {% if   colourMode == 'orientation' %} geomOrient     = orient;
  {% elif colourMode == 'vertexData' %}  geomVertexData = vertexData;
  {% elif colourMode == 'imageData' %}   geomVertex     = vertex;
  {% endif %}

  {% if clipMode == 'vertexData' %}
  geomClipVertexData = clipVertexData;
  {% endif %}

  gl_Position = MVP * vec4(vertex, 1);
}
