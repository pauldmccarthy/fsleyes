/*
 * Vertex shader used by RenderTexture instances which use
 * a depth texture.
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
