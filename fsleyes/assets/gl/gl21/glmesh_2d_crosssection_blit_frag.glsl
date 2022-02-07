/*
 * Fragment shader used by the GLMesh for drawing 2D cross sections.
 * Colours all fragments with a flat colour.
 */
#version 120

uniform vec4 colour;

void main(void) {
  gl_FragColor = colour;
}
