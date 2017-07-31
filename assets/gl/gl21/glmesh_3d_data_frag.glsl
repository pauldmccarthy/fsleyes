/*
 * Fragment shader used for drawing 3D GLMesh objects.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include glmesh_data_common.glsl
#pragma include glmesh_3d_lighting.glsl

uniform bool lighting;
uniform vec3 lightPos;
varying vec3 fragVertex;
varying vec3 fragNormal;


void main(void) {

  vec4 colour = glmesh_data_colour();

  if (lighting) {

    colour.rgb = mesh_lighting(fragVertex, fragNormal, lightPos, colour.rgb);
  }

  gl_FragColor = colour;
}
