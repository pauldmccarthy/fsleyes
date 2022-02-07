/*
 * Fragment shader for GL canvas annotations.
 */
#version 120

uniform vec4 colour;

void main(void) {
  gl_FragColor = colour;
}
