/*
 * OpenGL vertex shader used by the Scene3DCanvas for blending
 * rendered overlays into a single scene.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec2 texCoord;
varying   vec2 fragTexCoord;

void main(void) {

  fragTexCoord = texCoord;
  gl_Position  = vec4(vertex, 1);
}
