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
{% if shaderType == 'orientation' %}
in  vec3 orient;
out vec3 geomOrient;
{% elif shaderType == 'vertexData' %}
in  float vertexData;
out float geomVertexData;
{% elif shaderType == 'imageData' %}
out vec3 geomVertex;
{% endif %}


void main(void) {
  {% if shaderType == 'orientation' %}
  geomOrient = orient;
  {% elif shaderType == 'vertexData' %}
  geomVertexData = vertexData;
  {% elif shaderType == 'imageData' %}
  geomVertex = vertex;
  {% endif %}
  gl_Position = MVP * vec4(vertex, 1);
}
