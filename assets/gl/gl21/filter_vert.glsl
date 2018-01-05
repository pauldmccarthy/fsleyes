/*
 * Vertex shader used by filter shaders (see the fsleyes.gl.shaders.filter
 * module).
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


attribute vec2 texCoord;
attribute vec3 vertex;
varying   vec2 fragTexCoord;


void main(void) {

  fragTexCoord = texCoord;
  gl_Position  = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
