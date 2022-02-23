/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to image data.
 */
#version 120

#pragma include gltractogram_data_common.glsl
#pragma include phong_lighting.glsl


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

/* Light position, and whether to apply lighting. */
uniform bool lighting;
uniform vec3 lightPos;

/* Vertex coordinates (in world space) */
varying vec3 fragVertexWorld;

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
  vec3 texCoord = (texCoordXform * vec4(fragVertexWorld, 1)).xyz;
  float val     = texture3D(imageTexture, texCoord).x;
  val           = val * voxScale + voxOffset;

  {% if clipMode == 'none' %}
  clipVal = val;
  {% elif clipMode == 'vertexData' %}
  clipVal = fragClipVertexData;
  {% elif clipMode == 'imageData' %}
  // TODO
  clipVal = val;
  {% endif %}

  vec4 colour = generateColour(val, clipVal);

  if (lighting) {
    colour.xyz = phong_lighting(fragVertex, fragNormal, lightPos, colour.xyz);
  }

  gl_FragColor = colour;
}
