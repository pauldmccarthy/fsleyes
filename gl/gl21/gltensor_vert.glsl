/*
 * OpenGL vertex shader used for rendering GLTensor instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

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

uniform bool lighting;

uniform vec3 lightDir;

attribute vec3  voxel;
attribute vec3  vertex;

varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;

varying vec4 fragColourFactor;


void main(void) {

  // Lookup the tensor parameters from the textures
  vec3 texCoord = (voxel + 0.5) / imageShape;
  vec3 light;

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

  // Transform the sphere by the tensor
  // eigenvalues and eigenvectors, and
  // shift it by the voxel coordinates
  // to transform it in to the image
  // voxel coordinate system.
  //
  // See these web pages for details
  // on drawing ellipsoids:
  //
  //   - http://archive.gamedev.net/archive/reference/  \
  //     programming/features/superquadric/index.html
  //
  //   - paulbourke.net/geometry/circlesphere/
  vec3 pos     = vertex;
  mat3 eigvecs = mat3(v1, v2, v3);

  // TODO scale by the range of l1/l2/l3
  pos.x *= l1 * 150;
  pos.y *= l2 * 150;
  pos.z *= l3 * 150;
  pos    = eigvecs * pos;
  pos   += voxel;

  if (lighting) {

    // Calculate the normal
    // vector for this vertex.
    vec3 norm = vertex;
    norm.x   /= l1;
    norm.y   /= l2;
    norm.z   /= l3;

    // The matrix made up of the eigenvectors
    // should be orthonormal, so can be used
    // to transform the vertex surface normals.
    //
    // [ orthonormal -> eigvecs = T(I(eigvecs)) ]
    norm      = eigvecs * norm;

    // GLSL 1.20 calculates the normal
    // matrix for us; we will have to
    // calculate it ourselves if we move
    // to a more modern version of GLSL.
    norm     = gl_Normal * norm;

    norm = normalize(norm);

    // Calculate the diffuse and
    // ambient light components
    float ambient = 0.1;
    float diffuse = clamp(dot(norm, -lightDir), 0, 1);

    diffuse = (diffuse + ambient);
    light   = vec3(diffuse, diffuse, diffuse);
  }
  
  else
    light = vec3(1, 1, 1);

  // Transform from voxels into display
  gl_Position = gl_ModelViewProjectionMatrix *
                voxToDisplayMat              *
                vec4(pos, 1);

  fragVoxCoord     = floor(voxel + 0.5);
  fragTexCoord     = texCoord;
  fragColourFactor = vec4(light, 1);
}
