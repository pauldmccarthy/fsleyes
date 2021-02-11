/*
 * Fragment shader used for drawing 3D GLMeshes with a flat colour.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120
#pragma include phong_lighting.glsl

/* Colour to use. */
uniform vec4 colour;

/* Toggle lighting */
uniform bool lighting;
uniform vec3 lightPos;

/* Vertex */
varying vec3 fragVertex;

/* Vertex normal */
varying vec3 fragNormal;

/* Light position transformed by the model view matrix */
varying vec3 fragLightPos;


void main(void) {

  vec4 finalColour = colour;

  if (lighting) {
    finalColour.rgb = phong_lighting(fragVertex,
                                     fragNormal,
                                     fragLightPos,
                                     finalColour.rgb);
  }

  gl_FragColor = finalColour;
}
