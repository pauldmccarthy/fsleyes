/*
 * OpenGL vertex shader used for rendering GLCSD 
 * instances - spherical deconvolution of diffusion 
 * data.
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
 * Image shape (x, y, z).
 */
uniform vec3 imageShape;

/*
 * Enable/disable lighting.
 */
uniform bool lighting;

/*
 * Position of the light - must 
 * be specified in eye/screen space.
 */
uniform vec3 lightPos;

/*
 * Number of vertices used to draw the 
 * sphere at each voxel.
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

    /*
     * Look up the radius for this vertex. The 
     * gl_InstanceID gives us the voxel number,
     * and vertex ID gives us the location of
     * this vertex on the sphere. We need to turn
     * this 1D index into 3D texture coordinates.
     */
    int  flatIdx = gl_InstanceID * nVertices + gl_VertexID;
    vec3 radIdx  = roll3D(flatIdx, radTexShape);
    radIdx       = (radIdx + 0.5) / radTexShape;
    float radius = texture3D(radTexture, radIdx).r;

    /* Neurological flip if necessary */
    if (xFlip)
      pos.x = -pos.x;

    /* 
     * Adjust the position of this vertex
     * relative to the sphere centre, and 
     * then translate it to its voxel.
     */
    pos     = pos * radius * sizeScaling;
    pos    += voxel;
  
    /* Apply lighting if it is enabled */
    vec3 light;
    if (lighting) {
      light = vec3(1, 1, 1);
    }
  
    /*
     * If lighting is not enabled, the
     * fragment colour is not modified.
     */
    else {
      light = vec3(1, 1, 1);
    }

    /*
     * Transform the vertex from the
     * voxel coordinate system into
     * the display coordinate system.
     */
    gl_Position = gl_ModelViewProjectionMatrix *
                  voxToDisplayMat              *
                  vec4(pos, 1);
  
    /*
     * Send the voxel coordinates, vertex radius, and
     * the colour scaling factor to the fragment shader.
     */
    fragVoxCoord     = floor(voxel + 0.5);
    fragColourFactor = vec4(light, 1);
    fragRadius       = radius;
    fragVertex       = vertex * radius;
}
