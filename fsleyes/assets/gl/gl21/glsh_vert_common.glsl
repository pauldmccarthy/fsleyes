/*
 * This file contains logic for rendering GLSH instances
 * (Fibre orientation distributions). It is used by the 
 * glsh_vert.glsl and glsh_volume_vert.glsl vertex shaders.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

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
 * Position of the light - must 
 * be specified in eye/screen space.
 */
uniform vec3 lightPos;


/*
 * Texture containing radius values for each 
 * displayed voxel/vertex.  This texture is 
 * only 3D for convenience - it is interpreted 
 * as a 1D vector of radius values.
 */
uniform sampler3D radTexture;


/*
 * Shape of the radius texture.
 */
uniform vec3 radTexShape;


/*
 * Transformation matrix from radius texture 
 * values to their original values.
 */
uniform mat4 radXform;


/*
 * Enable/disable lighting.
 */
uniform bool lighting;

/*
 * Number of vertices used to draw 
 * the sphere at each voxel.
 */
uniform int nVertices;

/*
 * Scaling factor used to scale the  
 * sphere size.
 */
uniform float sizeScaling;

/*
 * If true, the spheres in each voxel
 * are flipped along the x axis.
 */
uniform bool xFlip;


/*
 * Voxel coordinates corresponding to the 
 * current vertex.
 */
attribute vec3 voxel;


/*
 * The current vertex on a unit sphere. The vertex
 * position will be adjusted by its radius (which
 * is looked up in the radTexture).
 */
attribute vec3 vertex;


/*
 * Indices for the current voxel, and the current 
 * vertex within the current voxel. These are 
 * built-in (as gl_InstanceID and gl_VertexID) in 
 * more recent versions of GLSL.
 */
attribute float voxelID;
attribute float vertexID;


/*
 * Adjust the given vertex position by its 
 * radius, and returns the radius value.
 */
float adjustPosition(inout vec3 pos) {

    /*
     * Look up the radius for this vertex. The 
     * gl_InstanceID gives us the voxel number,
     * and vertex ID gives us the location of
     * this vertex on the sphere. We need to turn
     * this 1D index into 3D texture coordinates.
     */
    int  flatIdx = int(voxelID * nVertices + vertexID);
    vec3 radIdx  = roll3D(flatIdx, radTexShape);
    radIdx       = (radIdx + 0.5) / radTexShape;
    float radius = texture3D(radTexture, radIdx).r;

    radius = radius * radXform[0].x + radXform[3].x;

    /* Neurological flip if necessary */
    if (xFlip)
      pos.x = -pos.x;

    /* 
     * Adjust the position of this vertex
     * relative to the sphere centre, and 
     * then translate it to its voxel.
     */
    pos  = pos * radius * sizeScaling;
    pos += voxel;

    return radius;
}

/*
 * Calculates lighting for the current vertex. 
 *
 * Note: This is broken.
 */
vec3 calcLighting(in float radius) {
  
    vec3 light;
    if (lighting) {
  
      vec3 norm   = normalize(normalMatrix * vertex * radius);
      float angle = dot(norm, -lightPos);

      float diffuse = max(angle * angle, 0);
      diffuse      += 0.3;

      light = vec3(diffuse, diffuse, diffuse);
    } 
    /*
     * If lighting is not enabled, the
     * fragment colour is not modified.
     */
    else {
      light = vec3(1, 1, 1);
    }

    return light;
}
