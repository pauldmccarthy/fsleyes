/*
 * OpenGL vertex shader used for rendering GLSH instances, 
 * where the FODs are coloured by direction or radius.
 *
 * Most logic is in glsh_vert_common.glsl.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include roll.glsl
#pragma include glsh_vert_common.glsl

/*
 * Transformation matrix which transforms voxel 
 * coordinates into the display coordinate system.
 */
uniform mat4 voxToDisplayMat;


/*
 * Image shape (x, y, z).
 */
uniform vec3 imageShape;


/*
 * Voxel coordinate passed through to the fragment shader.
 */
varying vec3 fragVoxCoord;

/*
 * Corresponding texture coordinates.
 */
varying vec3 fragTexCoord;

/*
 * Multiplicative colour factor passed through to the 
 * fragment shader, used for lighting.
 */
varying vec4 fragColourFactor;

/*
 * Vertex location and radius, passed through to the 
 * fragment shader.
 */
varying float fragRadius;
varying vec3  fragVertex;


void main(void) {

    vec3  pos    = vertex;
    float radius = adjustPosition(pos);
    vec3  light  = calcLighting(radius);
  
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
    fragTexCoord     = (voxel + 0.5) / imageShape;
    fragColourFactor = vec4(light, 1);
    fragRadius       = radius;
    fragVertex       = vertex * radius;
}
