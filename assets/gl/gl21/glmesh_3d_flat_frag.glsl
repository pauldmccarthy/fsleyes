/*
 * Fragment shader used for drawing 3D GLMeshes with a flat colour.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120
#pragma include glmesh_3d_lighting.glsl

/* Colour to use. */
uniform vec4 colour;

/* Toggle lighting */
uniform bool lighting;


/* Toggle lighting */
uniform vec3 lightPos;


/* Vertex */
varying vec3 fragVertex;


/* Vertex normal */
varying vec3 fragNormal;


void main(void) {

  vec4 finalColour = colour;

  if (lighting) {

    finalColour.rgb = mesh_lighting(fragVertex,
                                    fragNormal,
                                    lightPos,
                                    finalColour.rgb);
  }

  gl_FragColor = finalColour;
}
