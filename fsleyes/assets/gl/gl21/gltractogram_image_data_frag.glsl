/*
 * Fragment shader for colouring GLTractogram instances,
 * where streamlines are coloured according to image data.
 */
#version 120

#pragma include gltractogram_data_common.glsl


/*
 * Image texture to get data from, scale/
 * offset to transform from texture data
 * range to original data range, and affine
 * to transform from vertex coordinates to
 * image texture coordinates.
 */
uniform sampler3D imageTexture;
uniform float     voxScale;
uniform float     voxOffset;
uniform mat4      texCoordXform;

/* Vertex coordinates */
varying vec3 fragData;

void main(void) {
  vec3 texCoord = (texCoordXform * vec4(fragData, 1)).xyz;
  float val     = texture3D(imageTexture, texCoord).x;
  val           = val * voxScale + voxOffset;
  gl_FragColor  = generateColour(val);
}
