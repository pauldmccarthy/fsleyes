/*
 * Vertex shader used by RenderTexture instances which use
 * a depth texture.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

varying vec2 fragTexCoord;

void main(void) {

  fragTexCoord = gl_MultiTexCoord0.xy;
  gl_Position  = gl_ModelViewProjectionMatrix * vec4(gl_Vertex.xyz, 1);
}
