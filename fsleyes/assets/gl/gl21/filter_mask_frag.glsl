/*
 * A filter fragment shader which masks the output by the alpha values
 * in a texture.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform sampler2D texture;
uniform sampler2D mask;

varying vec2 texCoord;

void main(void) {

  vec4 maskval = texture2D(mask, texCoord);

  if (maskval.a == 0) {
    discard;
  }
  else {
    gl_FragColor = vec4(texture2D(texture, texCoord).rgb, 1);
  }
}
