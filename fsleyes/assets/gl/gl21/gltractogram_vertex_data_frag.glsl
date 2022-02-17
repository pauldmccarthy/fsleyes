/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to per-vertex
 * scalar data.
 */
#version 120

#pragma include gltractogram_data_common.glsl


/* Vertex data value */
varying float fragData;


void main(void) {
  gl_FragColor = generateColour(fragData);
}
