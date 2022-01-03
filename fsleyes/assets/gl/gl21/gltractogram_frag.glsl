/*
 * Fragment shader for colouring GLTractogram instances.
 */
#version 120


/* Vertex coordinates corresponding to this fragment. */
varying vec3 fragVertex;

/* Streamline orientation corresponding to this fragment. */
varying vec3 fragOrient;


void main(void) {

  gl_FragColor = vec4(fragOrient, 1);
}
