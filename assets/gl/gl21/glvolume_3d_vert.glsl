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

/*
 * Transformation matrix to transform image texture
 * coordinates into clip image texture coordinates.
 */
uniform mat4 clipCoordXform;

varying vec3 fragTexCoord;
varying vec3 fragClipTexCoord;

void main(void) {

  fragTexCoord     = texCoord;
  fragClipTexCoord = (clipCoordXform * vec4(texCoord, 1)).xyz;

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
