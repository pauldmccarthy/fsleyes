/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to per-vertex
 * scalar data.
 */
#version 120

#pragma include gltractogram_data_common.glsl

{% if lighting %}
#pragma include phong_lighting.glsl
{% endif %}


/* Vertex data value for colouring */
varying float fragVertexData;

{% if clipMode == 'vertexData' %}
/* Vertex data value for clipping*/
varying float fragClipVertexData;

{% elif clipMode == 'imageData' %}
/*
 * Image texture containing clipping values,
 * scale/offset to transform from texture
 * value range to original value range, and
 * affine to transform vertex coordinates
 * into clip texture coordinates.
 */
uniform sampler3D clipTexture;
uniform float     clipValScale;
uniform float     clipValOffset;
uniform mat4      clipTexCoordXform;

/* Vertex coordinates, before MVP transformation */
varying vec3      fragVertexWorld;
{% endif %}


{% if lighting %}
/* Light position, and whether to apply lighting. */
uniform bool lighting;
uniform vec3 lightPos;

/*
 * Vertex coordinates and normal (in NDC space),
 * for calculating lighting.
 */
varying vec3 fragVertex;
varying vec3 fragNormal;
{% endif %}


void main(void) {
  float clipVal;

  {% if clipMode == 'none' %}
  /* Clip fragment according to the value used for colouring it */
  clipVal = fragVertexData;

  {% elif clipMode == 'vertexData' %}
  /* Clip fragment according to the separate vertex clipping value */
  clipVal = fragClipVertexData;

  {% elif clipMode == 'imageData' %}
  /* Clip fragment acoording to value taken from clip texture */
  vec3 clipTexCoord = (clipTexCoordXform * vec4(fragVertexWorld, 1)).xyz;
  clipVal           = texture3D(clipTexture, clipTexCoord).x;
  clipVal           = clipVal * clipValScale + clipValOffset;
  {% endif %}

  vec4 colour = generateColour(fragVertexData, clipVal);

  {% if lighting %}
  if (lighting) {
    colour.xyz = phong_lighting(fragVertex, fragNormal, lightPos, colour.xyz);
  }
  {% endif %}
  gl_FragColor = colour;
}
