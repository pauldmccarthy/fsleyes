/*
 * Fragment shader used for drawing 2D GLMesh cross-sections when the vertices
 * are coloured according to some data.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include glmesh_data_common.glsl

void main(void) {

  gl_FragColor = glmesh_data_colour();
}
