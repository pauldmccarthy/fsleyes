/*
 * Vertex shader for rendering GLTractogram instances.
 */
#version 120

uniform mat4 MVP;

/* Streamline vertex coordinates. */
attribute vec3 vertex;

{% if twod %}
/*
 * Current vertex coordinate on circle
 * used to draw the current streamline
 * point, defined in normalised device
 * coordinates.
 */
attribute vec3 circleVertex;
{% endif %}

/* Unused */
uniform int  resolution;
uniform bool lighting;

{% if colourMode == 'orientation' %}
/*
 * Per-vertex orientation, used for colouring,
 * passed through to fragment shader.
 */
attribute vec3 orient;
varying   vec3 fragOrient;

{% elif colourMode == 'vertexData' %}
/*
 * Per-vertex data value, used for colouring,
 * passed through to fragment shader.
 */
attribute float vertexData;
varying   float fragVertexData;
{% endif %}

{% if colourMode == 'imageData' or clipMode == 'imageData' %}
/*
 * Input vertex coordinates, passed
 * through to fragment shader.
 */
varying vec3 fragVertexWorld;
{% endif %}

{% if clipMode == 'vertexData' %}
/*
 * Per-vertex data for clipping, passed
 * through to fragment shader.
 */
attribute float clipVertexData;
varying   float fragClipVertexData;
{% endif %}


void main(void) {

  {% if colourMode == 'orientation' %}
  fragOrient = orient;
  {% elif colourMode == 'vertexData' %}
  fragVertexData = vertexData;
  {% endif %}

  {% if colourMode == 'imageData' or clipMode == 'imageData' %}
  fragVertexWorld = vertex;
  {% endif %}

  {% if clipMode == 'vertexData' %}
  fragClipVertexData = clipVertexData;
  {% endif %}

  {% if twod %}
  gl_Position = MVP * vec4(vertex, 1) + vec4(circleVertex, 0);
  {% else %}
  gl_Position = MVP * vec4(vertex, 1);
  {% endif %}
}
