/*
 * OpenGL vertex shader used for rendering GLTensor instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * Textures containing the eigenvectors (v1, v2, v3) 
 * and eigenvalues (l1, l2, l3) of the diffusion 
 * tensor matrix.
 */
uniform sampler3D v1Texture;
uniform sampler3D v2Texture;
uniform sampler3D v3Texture;
uniform sampler3D l1Texture;
uniform sampler3D l2Texture;
uniform sampler3D l3Texture;

/*
 * Transforms (scales/offsets) for transforming from 
 * data in the above textures to their original data 
 * range.
 */
uniform mat4 v1ValXform;
uniform mat4 v2ValXform;
uniform mat4 v3ValXform;
uniform mat4 l1ValXform;
uniform mat4 l2ValXform;
uniform mat4 l3ValXform;

/*
 * Transformation matrix which transforms voxel 
 * coordinates into the display coordinate system.
 */
uniform mat4 voxToDisplayMat;

/*
 * Matrices to transform from vector 
 * texture coordinates to colour/clip/
 * modulate image texture coordinates.
 */
uniform mat4 colourCoordXform;
uniform mat4 clipCoordXform;
uniform mat4 modCoordXform;

/*
 * Transformation matrix which transforms normal 
 * vectors. This should be set to the transpose
 * of the inverse of the model-view matrix (see
 * http://www.scratchapixel.com/lessons/\
 * mathematics-physics-for-computer-graphics/\
 * geometry/transforming-normals for a good 
 * explanation).
 */
uniform mat3 normalMatrix;

/*
 * Image shape (x, y, z).
 */
uniform vec3 imageShape;

/*
 * Scaling factor for eigenvalues - this controls 
 * the maximum size that any tensor ellipsoid is 
 * drawn. Set this to:
 * 
 *   0.5 / max(abs(l1))
 * 
 * to make the maximum ellipsoid circumference the 
 * size of one voxel.
 */
uniform float eigValNorm;

/*
 * Enable/disable a simple directional lighting model.
 */
uniform bool lighting;

/*
 * Position of the directional light - must be 
 * specified in eye/screen space.
 */
uniform vec3 lightPos;

/*
 * If true, the V1, V2 and V3 eigenvectors 
 * are flipped about the x axis.
 */
uniform bool xFlip;

/*
 * Voxel corresponding to the current vertex.
 */
attribute vec3 voxel;

/*
 * The current vertex on a unit sphere. The vertex
 * will be transformed into an ellipsoid using the 
 * tensor matrix eigen-decomposition.
 */
attribute vec3 vertex;

/*
 * Voxel coordinate passed through to the fragment shader.
 */
varying vec3 fragVoxCoord;

/*
 * Vector image texture coordinate passed through to the 
 * fragment shader.
 */
varying vec3 fragVecTexCoord;

/*
 * Colour/clip/modulate image texture coordinates.
 */
varying vec3 fragTexCoord;
varying vec3 fragClipTexCoord;
varying vec3 fragModTexCoord;


/*
 * Multiplicative colour factor passed through to the 
 * fragment shader, used for lighting.
 */
varying vec4 fragColourFactor;


void main(void) {

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

  // Invert the vectors about
  // the x axis if necessary
  if (xFlip) {
    v1.x = -v1.x;
    v2.x = -v2.x;
    v3.x = -v3.x;
  }

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

  // Scale the ellipsoid by a constant
  // factor (calculated in gltensor_funcs)
  pos.x *= l1 * eigValNorm;
  pos.y *= l2 * eigValNorm;
  pos.z *= l3 * eigValNorm;
  pos    = eigvecs * pos;
  pos   += voxel;


  // Apply lighting if it is enabled
  vec3 light;
  if (lighting) {

    // Calculate the normal
    // vector for this vertex.
    vec3 norm = vertex;

    // Divide by the ellipsoid radii
    // to get the normal of a point
    // on the surface
    norm.x /= l1;
    norm.y /= l2;
    norm.z /= l3;

    // The eigenvector matrix should only
    // define rotations and scalings (not
    // reflections), so here we make sure
    // that it has a positive determinant.
    float det = eigvecs[0][0] * eigvecs[1][1] * eigvecs[2][2] +
                eigvecs[0][1] * eigvecs[1][2] * eigvecs[2][0] +
                eigvecs[1][0] * eigvecs[2][1] * eigvecs[0][2] -
                eigvecs[2][0] * eigvecs[1][1] * eigvecs[0][2] -
                eigvecs[0][0] * eigvecs[1][2] * eigvecs[2][1] -
                eigvecs[0][1] * eigvecs[1][0] * eigvecs[2][2];

    // The matrix is orthonormal, so
    // inverting it should be enough
    // to invert the determinant.
    if (det < 0)
      eigvecs = -eigvecs;

    // Transform the normal vectors by eigvecs
    // to rotate them into the voxel coordinate
    // system, and then transform them by the
    // normal matrix to put them into display
    // space.
    //
    // The eigvecs matrix should be orthonormal,
    // so can be used to transform the vertex
    // surface normals. The normalMatrix is
    // calculated for us in gltensor_funcs.
    //
    // [ orthonormal -> eigvecs = T(I(eigvecs)) ]
    norm = normalize(normalMatrix * eigvecs * norm);


    // I honestly have no idea why this is necessary.
    // There is some weird interaction going on in the
    // transformation of the normal vectors from unit
    // sphere space to ellipsoid space (through the
    // eigvecs matrix), and then on to display space
    // (through the normalMatrix).
    //
    // If the eigvecs matrix has a negative determinant,
    // we need to flip the xy values of the normal vector.
    //
    // If we don't do this, the lighting direction on
    // ellipsoids with positive/negative determinants
    // is inverted. I don't know what the hell is going
    // on here.
    if (det < 0)
       norm.xy = -norm.xy;

    float angle   = dot(norm, -lightPos);

    // More hackiness - I'm squaring the angle
    // for a more dramatic lighting effect, but
    // am not discarding negative values. Banding
    // will occur if the light direction is near
    // parallel to the xy plane.
    float diffuse = max(angle * angle, 0);

    // Add an ambient light level of 30%
    diffuse = diffuse + 0.3;
    light   = vec3(diffuse, diffuse, diffuse);
  }

  // If lighting is not enabled, the
  // fragment colour is not modified.
  else
    light = vec3(1, 1, 1);

  // Transform the vertex from the
  // voxel coordinate system into
  // the display coordinate system.
  gl_Position = gl_ModelViewProjectionMatrix *
                voxToDisplayMat              *
                vec4(pos, 1);

  // Send the voxel and texture coordinates, and
  // the colour scaling factor to the fragment shader.
  fragVoxCoord     = floor(voxel + 0.5);
  fragVecTexCoord  = texCoord;
  fragTexCoord     = (colourCoordXform * vec4(texCoord, 1)).xyz;
  fragClipTexCoord = (clipCoordXform   * vec4(texCoord, 1)).xyz;
  fragModTexCoord  = (modCoordXform    * vec4(texCoord, 1)).xyz; 
  fragColourFactor = vec4(light, 1);
}
