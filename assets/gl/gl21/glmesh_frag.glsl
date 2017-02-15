/*
 * Fragment shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com> 
 */
#version 120

uniform sampler1D cmap;
uniform mat4      cmapXform;
uniform float     clipLow;
uniform float     clipHigh;
varying float     fragVertexData;

void main(void) {

  if (fragVertexData <= clipLow || fragVertexData >= clipHigh) {
    discard;
  }

  float texCoord = (cmapXform * vec4(fragVertexData, 0, 0, 1)).x;
  gl_FragColor   = texture1D(cmap, texCoord);
}
