/*
 * Fragment shader used for drawing GLMeshes in 2D with a flat colour.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform vec4 colour;

void main(void) {
  gl_FragColor = colour;
}
