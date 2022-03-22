/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to their
 * orientation.
 */
#version 120

{% if lighting %}
#pragma include phong_lighting.glsl
{% endif %}

/*
 * Colours used for X/Y/Z orientation, and
 * scale/offset for applying global
 * brightness/contrast
 */
uniform vec4  xColour;
uniform vec4  yColour;
uniform vec4  zColour;
uniform float colourScale;
uniform float colourOffset;


{% if clipMode != 'none' %}
/*
 * Low/high clipping range, and whether
 * to clip outside or inside the range.
 */
uniform bool  invertClip;
uniform float clipLow;
uniform float clipHigh;
{% endif %}

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

/* Vertex coordinates, before MVP transformation */
varying vec3      fragVertexWorld;
{% endif %}

/* Streamline orientation corresponding to this fragment. */
varying vec3 fragOrient;

/*
 * Light position, and whether lighting
 * effect should be applied.
 */
{% if lighting %}
uniform vec3 lightPos;
uniform bool lighting;
/*Vertex position and vertex normal, used for lighting. */
varying vec3 fragNormal;
varying vec3 fragVertex;
{% endif %}


void main(void) {

  {% if clipMode != 'none' %}
  float clipVal;
  {% endif %}

  {% if clipMode == 'vertexData' %}
  /* Clip fragment acoording to per-vertex data */
  clipVal = fragClipVertexData;

  {% elif clipMode == 'imageData' %}
  /* Clip fragment acoording to value taken from clip texture */
  vec3 clipTexCoord = (clipTexCoordXform * vec4(fragVertexWorld, 1)).xyz;
  clipVal           = texture3D(clipTexture, clipTexCoord).x;
  clipVal           = clipVal * clipValScale + clipValOffset;
  {% endif %}

  {% if clipMode != 'none' %}
  if ((!invertClip && (clipVal <= clipLow || clipVal >= clipHigh)) ||
      ( invertClip && (clipVal >= clipLow && clipVal <= clipHigh))) {
    discard;
  }
  {% endif %}

  vec4 colour = fragOrient.x * xColour +
                fragOrient.y * yColour +
                fragOrient.z * zColour;
  colour.xyz  = colour.xyz * colourScale + colourOffset;
  colour.a    = (xColour.a +
                 yColour.a +
                 zColour.a) / 3;

  {% if lighting %}
  if (lighting) {
    colour.xyz = phong_lighting(fragVertex, fragNormal, lightPos, colour.xyz);
  }
  {% endif %}

  gl_FragColor = colour;
}
