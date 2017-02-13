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
  vec3 left  = texture2D(texture, vec2(x - xoff, y)).rgb;
  vec3 right = texture2D(texture, vec2(x + xoff, y)).rgb;
  vec3 above = texture2D(texture, vec2(x,        y + yoff)).rgb;
  vec3 below = texture2D(texture, vec2(x,        y - yoff)).rgb;

  rgba.rgb = (rgba.rgb + 0.5 * (left + right + above + below)) / 3.0;

  gl_FragColor = rgba;
}
