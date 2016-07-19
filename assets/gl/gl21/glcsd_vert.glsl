/*
 * OpenGL vertex shader used for rendering GLCSD instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120
#extension GL_EXT_gpu_shader4 : require

#pragma include roll.glsl



/*
 * Transformation matrix which transforms voxel 
 * coordinates into the display coordinate system.
 */
uniform mat4 voxToDisplayMat;

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


uniform sampler3D radTexture;


uniform vec3 radTexShape;

/*
 * Image shape (x, y, z).
 */
uniform vec3 imageShape;

/*
 * Enable/disable a simple directional lighting model.
 */
uniform bool lighting;

/*
 * Position of the directional light - must be 
 * specified in eye/screen space.
 */
uniform vec3 lightPos;



uniform int nVertices;


uniform int sizeScaling;




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
 * 
 */
attribute vec3 vertex;

/*
V * Voxel coordinate passed through to the fragment shader.
 */
varying vec3 fragVoxCoord;

/*
 * Texture coordinate passed through to the fragment shader.
 */
varying vec3 fragTexCoord;

/*
 * Multiplicative colour factor passed through to the 
 * fragment shader, used for lighting.
 */
varying vec4 fragColourFactor;


varying float fragRadius;
varying vec3  fragVertex;


void main(void) {

    vec3 pos = vertex;

    int  flatVoxel = unroll3D(voxel,                  imageShape);
    vec3 radIdxs   = roll3D(  flatVoxel * nVertices + gl_VertexID, radTexShape);
    radIdxs = (radIdxs + 0.5) / radTexShape;

    float radius = texture3D(radTexture, radIdxs).r;
  
    pos     = pos * radius * sizeScaling;
    pos    += voxel;
  
    // Apply lighting if it is enabled
    vec3 light;
    if (lighting) {
      light = vec3(1, 1, 1);
    }
  
    // If lighting is not enabled, the
    // fragment colour is not modified.
    else {
      light = vec3(1, 1, 1);
    }
  
    // Transform the vertex from the
    // voxel coordinate system into
    // the display coordinate system.
    gl_Position = gl_ModelViewProjectionMatrix *
                  voxToDisplayMat              *
                  vec4(pos, 1);
  
    // Send the voxel and texture coordinates, and
    // the colour scaling factor to the fragment shader.
    fragVoxCoord     = floor(voxel + 0.5);
    fragColourFactor = vec4(light, 1);
    fragRadius       = radius;
    fragVertex       = vertex * radius;
}
