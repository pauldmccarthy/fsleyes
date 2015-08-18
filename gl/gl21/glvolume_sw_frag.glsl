/*
 * Fast but limited OpenGL fragment shader used by
 * fsl/fslview/gl/gl21/glvolume_funcs.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

/*
 * image data texture.
 */
uniform sampler3D imageTexture;

/*
 * Texture containing the colour map.
 */
uniform sampler1D colourTexture;


/*
 * Shape of the imageTexture.
 */
uniform vec3 imageShape;

/*
 * Transformation matrix to apply to the voxel value,
 * so it can be used as a texture coordinate in the
 * colourTexture.
 */
uniform mat4 voxValXform;

/*
 * Clip voxels below this value.
 */
uniform float clipLow;

/*
 * Clip voxels above this value.
 */
uniform float clipHigh;


/*
 * Corresponding texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    /*
     * Look up the voxel value 
     */
    float voxValue = texture3D(imageTexture, fragTexCoord).r;

    /*
     * Clip out of range voxel values
     */
    if (voxValue < clipLow || voxValue > clipHigh) {
      
      gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
      return;
    }

    /*
     * Transform the voxel value to a colour map texture
     * coordinate, and look up the colour for the voxel value
     */
    voxValue     = voxValXform[0].x * voxValue + voxValXform[3].x;
    gl_FragColor = texture1D(colourTexture, voxValue);
}
