/*
 * Fast (but extremely limited) OpenGL fragment shader used for rendering
 * GLLabel instances. Outline/border mode is not supported.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

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
 * Image texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    float voxValue = texture3D(imageTexture, fragTexCoord).r;
    float lutCoord = ((voxValXform * vec4(voxValue, 0, 0, 1)).x + 0.5) / numLabels;
    
    gl_FragColor = texture1D(lutTexture, lutCoord);
}
