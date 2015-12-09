/*
 * OpenGL vertex shader used for rendering GLTensor instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#define PI      3.141592653589793
#define PI_ON_2 1.5707963267948966


/*
 Required inputs:

  - Textures containing V1, V2, V3 and L1, L2, L3

  - Voxel coordinates (these are the vertices)
  - Vertex index 
  - Ellipsoid resolution

  **We use (index % resolution) to calculate:**

  - U and V angles 

  - 

 */

uniform sampler3D v1Texture;
uniform sampler3D v2Texture;
uniform sampler3D v3Texture;
uniform sampler3D l1Texture;
uniform sampler3D l2Texture;
uniform sampler3D l3Texture;

uniform mat4 v1ValXform;
uniform mat4 v2ValXform;
uniform mat4 v3ValXform;
uniform mat4 l1ValXform;
uniform mat4 l2ValXform;
uniform mat4 l3ValXform;

uniform mat4 voxToDisplayMat;

uniform vec3 imageShape;

uniform float resolution;

attribute float index;
attribute vec3  voxel;

varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;


vec3 ellipsoidVertex(float l1, float l2, float l3, float u, float v) {

  float cosu = cos(u);
  float cosv = cos(v);
  float sinu = sin(u);
  float sinv = sin(v);
  
  float spcu = sign(cosu) * pow(abs(cosu), 2);
  float spcv = sign(cosv) * pow(abs(cosv), 2);
  float spsu = sign(sinu) * pow(abs(sinu), 2);
  float spsv = sign(sinv) * pow(abs(sinv), 2);

  vec3 x;

  x.x = spcu * spcv;
  x.y = spcu * spsv;
  x.z = spsu;

  return x;
}



void main(void) {

  float umin = -PI_ON_2;
  float umax =  PI_ON_2;
  float vmin = -PI;
  float vmax =  PI;
  float ustep = (umax - umin) / resolution;
  float vstep = (vmax - vmin) / resolution;

  // Index of this vertex 
  // within the ellipsoid
  float ellipsoidIndex = mod(index, resolution);

  // Ellipsoid angles for this vertex
  float u = umin + ustep * ellipsoidIndex;
  float v = vmin + vstep * ellipsoidIndex;

  // Lookup the tensor parameters from the textures
  vec3 texCoord = (voxel + 0.5) / imageShape;

  vec3  v1 = texture3D(v1Texture, texCoord).xyz;
  vec3  v2 = texture3D(v2Texture, texCoord).xyz;
  vec3  v3 = texture3D(v3Texture, texCoord).xyz;
  float l1 = texture3D(l1Texture, texCoord).x;
  float l2 = texture3D(l2Texture, texCoord).x;
  float l3 = texture3D(l3Texture, texCoord).x;

  // Transform from normalised 
  // texture values to real values
  v1 = v1 * v1ValXform[0].x + v1ValXform[3].x;
  v2 = v2 * v2ValXform[0].x + v2ValXform[3].x;
  v3 = v3 * v3ValXform[0].x + v3ValXform[3].x;
  l1 = l1 * l1ValXform[0].x + l1ValXform[3].x;
  l2 = l2 * l2ValXform[0].x + l2ValXform[3].x;
  l3 = l3 * l3ValXform[0].x + l3ValXform[3].x;

  // Calculate the position of
  // this vertex on the ellipsoid.
  // Vertices are grouped into quads -
  // figure out what corner we're on
  vec3 pos;

  float corner = mod(ellipsoidIndex, 4);
  
  if      (corner == 0) pos = ellipsoidVertex(l1, l2, l3, u,         v);
  else if (corner == 1) pos = ellipsoidVertex(l1, l2, l3, u + ustep, v);
  else if (corner == 2) pos = ellipsoidVertex(l1, l2, l3, u + ustep, v + vstep);
  else if (corner == 3) pos = ellipsoidVertex(l1, l2, l3, u,         v + vstep);

  // Transform the vertex from
  // the fibre coordinate system
  // to the voxel coordinate system
  mat3 eigvecs = mat3(v1, v2, v3);
  
  pos = pos * eigvecs + voxel;

  // Transform from voxels into display
  gl_Position = gl_ModelViewProjectionMatrix *
                voxToDisplayMat              *
                vec4(pos, 1);

  fragVoxCoord = voxel;
  fragTexCoord = texCoord;
}
