/*
 * Filter fragment shader which performs basic smoothing on a texture.
 */
#version 120

uniform sampler2D texture;
uniform vec2      offset;

varying vec2      texCoord;

void main(void) {

  float x    = texCoord.x;
  float y    = texCoord.y;
  float xoff = offset.x;
  float yoff = offset.y;

  vec4 rgba  = texture2D(texture, vec2(x,        y));
  vec4 left  = texture2D(texture, vec2(x - xoff, y));
  vec4 right = texture2D(texture, vec2(x + xoff, y));
  vec4 above = texture2D(texture, vec2(x,        y + yoff));
  vec4 below = texture2D(texture, vec2(x,        y - yoff));

  if (left.a  == 0) left  = rgba;
  if (right.a == 0) right = rgba;
  if (above.a == 0) above = rgba;
  if (below.a == 0) below = rgba;

  rgba.rgb += 0.5 * (left.rgb + right.rgb + above.rgb + below.rgb);
  rgba.rgb /= 3;

  gl_FragColor = rgba;
}
