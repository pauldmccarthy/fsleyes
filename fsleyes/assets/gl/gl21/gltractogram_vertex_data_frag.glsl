/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to per-vertex
 * scalar data.
 */
#version 120

#pragma include gltractogram_data_common.glsl
#pragma include phong_lighting.glsl


/* Light position, and whether to apply lighting. */
uniform bool lighting;
uniform vec3 lightPos;

/* Vertex data value */
varying float fragVertexData;

{% if clipMode == 'vertexData' %}
varying float fragClipVertexData;
{% elif clipMode == 'imageData' %}
// TODO different image texture
{% endif %}

/*
 * Vertex coordinates and normal (in NDC space),
 * for calculating lighting.
 */
varying vec3 fragVertex;
varying vec3 fragNormal;


void main(void) {
  float clipVal;

  {% if clipMode == 'none' %}
  clipVal = fragVertexData;
  {% elif clipMode == 'vertexData' %}
  clipVal = fragClipVertexData;
  {% elif clipMode == 'imageData' %}
  // TODO
  clipVal = 1 / 0;
  {% endif %}

  vec4 colour = generateColour(fragVertexData, clipVal);
  if (lighting) {
    colour.xyz = phong_lighting(fragVertex, fragNormal, lightPos, colour.xyz);
  }
  gl_FragColor = colour;
}
