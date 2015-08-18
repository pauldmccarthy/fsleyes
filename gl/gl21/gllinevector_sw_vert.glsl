/*
 * OpenGL vertex shader used for rendering GLLineVector instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;

attribute vec3 texCoord;

varying vec3 fragTexCoord;

void main(void) {

  fragTexCoord = texCoord;

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
