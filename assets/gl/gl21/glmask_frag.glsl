/*
 * OpenGL fragment shader used for rendering GLLabel instances. This
 * is to be used with the glvolume_vert.glsl vertex shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

/*
 * Texture containing image data.
 */
uniform sampler3D imageTexture;

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
 * Threshold outside of which voxels will not be drawn.
 */
uniform vec2 threshold;

/*
 * Invert the thresholding logic.
 */
uniform bool invert;

/*
 * Use spline interpolation
 */
uniform bool useSpline;

/*
 * Mask colour
 */
uniform vec4 colour;

/*
 * Voxel coordinates.
 */
varying vec3 fragVoxCoord;

/*
 * Image texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    vec3  voxCoord = fragVoxCoord;
    float voxValue;

    if (!test_in_bounds(voxCoord, imageShape)) {
        discard;
    }

    if (useSpline) voxValue = spline_interp(imageTexture,
                                            fragTexCoord,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture, fragTexCoord).r;

    if ((!invert && (voxValue <= threshold.x || voxValue >= threshold.y)) ||
        ( invert && (voxValue >= threshold.x && voxValue <= threshold.y))) {
      discard;
    }

  gl_FragColor = colour;
}
