/*
 * OpenGL fragment shader used for rendering GLLabel instances. This
 * is to be used with the glvolume_vert.glsl vertex shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include edge.glsl
#pragma include test_in_bounds.glsl

/*
 * Texture containing image data.
 */
uniform sampler3D imageTexture;

/*
 * Texture containing lookup table colours.
 */
uniform sampler1D lutTexture;

/*
 * Transformation matrix which transforms image texture data into
 * its actual data range.
 */
uniform mat4 voxValXform;

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Total number of colours in the lookup table texture.
 */
uniform float numLabels;

/*
 * Show outline of labelled regions?
 */
uniform bool outline;

/*
 * Width of edges along each axis.
 */
uniform vec3 outlineOffsets;

/*
 * Voxel coordinates.
 */
varying vec3 fragVoxCoord;

/*
 * Image texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    vec3 voxCoord = fragVoxCoord;

    if (!test_in_bounds(voxCoord, imageShape)) {
        discard;
    }

    float voxValue;
    voxValue = texture3D(imageTexture, fragTexCoord).r;

    float lutCoord = ((voxValXform * vec4(voxValue, 0, 0, 1)).x + 0.5) / numLabels;

    if (lutCoord < 0 || lutCoord > 1) {
        discard;
    }
    
    vec4 colour = texture1D(lutTexture, lutCoord);

    float tol    = 0.001 / numLabels;
    bool  isEdge = edge3D(imageTexture, fragTexCoord, voxValue, tol, outlineOffsets);

    /* 
     * I want the fragment to be filled if outlines
     * are enabled, and the fragment lies on an edge,
     * or if outlines are disabled and the fragment
     * does not lie on an edge. The corresponding
     * boolean logic:
     * 
     *     (isEdge && outline) || !(isEdge || outline);
     *
     * is a negated exclusive or, which reduces
     * down to a simple equality test ...
     */
    if (isEdge == outline) gl_FragColor   = colour;
    else                   gl_FragColor.a = 0.0;
}
