/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to image data.
 */
#version 120

#pragma include gltractogram_data_common.glsl

{% if lighting %}
#pragma include phong_lighting.glsl
{% endif %}

/*
 * Image texture to get data from, scale/
 * offset to transform from texture data
 * range to original data range, and affine
 * to transform from vertex coordinates to
 * image texture coordinates.
 */
uniform sampler3D imageTexture;
uniform float     voxScale;
uniform float     voxOffset;
uniform mat4      texCoordXform;

/* Vertex coordinates, before MVP transformation */
varying vec3 fragVertexWorld;

{% if clipMode == 'vertexData' %}
/* Per-vertex clipping value */
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
  vec3 texCoord = (texCoordXform * vec4(fragVertexWorld, 1)).xyz;
  float val     = texture3D(imageTexture, texCoord).x;
  val           = val * voxScale + voxOffset;

  {% if clipMode == 'none' %}
  /* Clip fragment according to the value used for colouring */
  clipVal = val;

  {% elif clipMode == 'vertexData' %}
  /* Clip fragment according to the separate per-vertex value */
  clipVal = fragClipVertexData;

  {% elif clipMode == 'imageData' %}
  /* Clip fragment according to value from the separate clipping texture */
  vec3 clipTexCoord = (clipTexCoordXform * vec4(fragVertexWorld, 1)).xyz;
  clipVal           = texture3D(clipTexture, clipTexCoord).x;
  clipVal           = clipVal * clipValScale + clipValOffset;
  {% endif %}

  vec4 colour = generateColour(val, clipVal);

  {% if lighting %}
  if (lighting) {
    colour.xyz = phong_lighting(fragVertex, fragNormal, lightPos, colour.xyz);
  }
  {% endif %}

  gl_FragColor = colour;
}
