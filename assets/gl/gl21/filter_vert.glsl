/*
 * Vertex shader used by filter shaders (see the fsleyes.gl.shaders.Filter
 * class).
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

varying vec2 texCoord;

void main(void) {

  texCoord    = gl_MultiTexCoord0.xy;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
