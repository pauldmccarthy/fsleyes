/*
 * Filter fragment shader which renders an outline.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include edge.glsl

uniform sampler2D texture;
uniform vec2      offsets;
uniform bool      outline;
varying vec2      fragTexCoord;

void main(void) {

  vec4 colour = texture2D(texture, fragTexCoord);
  vec4 tol    = 1.0 / vec4(255, 255, 255, 255);
  bool isEdge = edge2D(texture, fragTexCoord, colour, tol, offsets);

  /*
   * If the fragment lies on an edge
   * colour it, otherwise clear it.
   */
  if (isEdge == outline) gl_FragColor = colour;
  else                   discard;
}
