/*
 * Fragment shader used by Texture2D instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform sampler2D tex;
varying vec2      fragTexCoord;

void main(void) {
  gl_FragColor = texture2D(tex, fragTexCoord);
}
