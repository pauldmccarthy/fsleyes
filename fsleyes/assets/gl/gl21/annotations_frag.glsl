/*
 * Fragment shader for GL canvas annotations.
 */
#version 120

varying vec4 fragColour;

void main(void) {
  gl_FragColor = fragColour;
}
