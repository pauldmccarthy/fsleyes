/*
 * Fragment shader used by RenderTexture instances which use
 * a depth texture.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform sampler2D depthTexture;
uniform sampler2D colourTexture;
varying vec2      fragTexCoord;

void main(void) {
  gl_FragColor = texture2D(colourTexture, fragTexCoord);
  gl_FragDepth = texture2D(depthTexture,  fragTexCoord).x;
}
