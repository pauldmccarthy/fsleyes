/*
 * OpenGL vertex shader used for rendering GLRGBVector instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec3 voxCoord;
attribute vec3 texCoord;

/*
 * Transformation matrices to transform image texture 
 * coordinates into clip/modulate image texture 
 * coordinates.
 */
uniform mat4 colourCoordXform;
uniform mat4 clipCoordXform;
uniform mat4 modCoordXform;


varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;
varying vec3 fragVecTexCoord;
varying vec3 fragClipTexCoord;
varying vec3 fragModTexCoord;
varying vec4 fragColourFactor;

void main(void) {

  fragVoxCoord     = voxCoord;
  fragVecTexCoord  = texCoord;
  fragTexCoord     = (colourCoordXform * vec4(texCoord, 1)).xyz;
  fragClipTexCoord = (clipCoordXform   * vec4(texCoord, 1)).xyz;
  fragModTexCoord  = (modCoordXform    * vec4(texCoord, 1)).xyz;
  fragColourFactor = vec4(1, 1, 1, 1);

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
