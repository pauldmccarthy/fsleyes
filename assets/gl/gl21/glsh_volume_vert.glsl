/*
 * OpenGL vertex shader used for rendering GLSH instances,
 * when the FODs are coloured according to the values in
 * a different image (and hence the glvolume fragment shader
 * is being used).
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
 * Matrices which transform vector image
 * texture coordinates to colour/clip
 * image texture coordinates.
 */
uniform mat4 colourCoordXform;
uniform mat4 clipCoordXform;

/*
 * Image shape (x, y, z).
 */
uniform vec3 imageShape;


/*
 * Voxel coordinate passed through to the fragment shader.
 */
varying vec3 fragVoxCoord;


/*
 * Corresponding colour image texture coordinates.
 */
varying vec3 fragTexCoord;

/*
 * Clip image texture coordinates.
 */
varying vec3 fragClipTexCoord;


/*
 * Multiplicative colour factor passed through to the
 * fragment shader, used for lighting.
 */
varying vec4 fragColourFactor;

/*
 * Expected by glvolume_frag.glsl, but not used
 */
varying vec3 fragModTexCoord;


void main(void) {

    vec3 pos      = vertex;
    float radius  = adjustPosition(pos);
    vec3 light    = calcLighting(radius);
    vec3 texCoord = (voxel + 0.5) / imageShape;

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
    fragTexCoord     = (colourCoordXform * vec4(texCoord, 1)).xyz;
    fragClipTexCoord = (clipCoordXform   * vec4(texCoord, 1)).xyz;
    fragModTexCoord  = vec3(0, 0, 0);
    fragColourFactor = vec4(light, 1);
}
