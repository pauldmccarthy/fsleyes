/*
 * OpenGL vertex shader used for rendering GLVolume instances in 3D.
 * All this shader does is set the vertex position, and pass the
 * texture coordinates through to the fragment shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec3 texCoord;

varying vec3 fragVertex;
varying vec3 fragTexCoord;

void main(void) {

  fragTexCoord = texCoord;
  fragVertex   = (gl_ModelViewMatrix * vec4(vertex, 1)).xyz;
  gl_Position  = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
