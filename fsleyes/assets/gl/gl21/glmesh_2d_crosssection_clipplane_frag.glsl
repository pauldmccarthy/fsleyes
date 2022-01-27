/*
 * Fragment shader used by the GLMesh for drawing 2D cross sections.
 * Clips fragments based on their intersection with a clipping plane.
 */
#version 120

varying float clipDistance;

void main(void) {

  if (clipDistance < 0) {
    discard;
  }

  gl_FragColor = vec4(1, 1, 1, 1);
}
