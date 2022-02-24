/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 330

uniform mat4 MVP;

/* Vertex coordinates. */
in vec3 vertex;

{% if colourMode == 'orientation' %}
/*
 * Per-vertex orientation, used for colouring,
 * passed through to fragment shader.
 */
in  vec3 orient;
out vec3 geomOrient;

{% elif colourMode == 'vertexData' %}
/*
 * Per-vertex data value, used for colouring,
 * passed through to fragment shader.
 */
in  float vertexData;
out float geomVertexData;
{% endif %}

{% if colourMode == 'imageData' or clipMode == 'imageData' %}
/*
 * Input vertex coordinates, passed
 * through to fragment shader.
 */
out vec3 geomVertex;
{% endif %}

{% if clipMode == 'vertexData' %}
/*
 * Per-vertex data for clipping, passed
 * through to fragment shader.
 */
in  float clipVertexData;
out float geomClipVertexData;
{% endif %}


void main(void) {

  {% if colourMode == 'orientation' %}
  geomOrient = orient;
  {% elif colourMode == 'vertexData' %}
  geomVertexData = vertexData;
  {% endif %}

  {% if colourMode == 'imageData' or clipMode == 'imageData' %}
  geomVertex = vertex;
  {% endif %}

  {% if clipMode == 'vertexData' %}
  geomClipVertexData = clipVertexData;
  {% endif %}

  gl_Position = MVP * vec4(vertex, 1);
}
