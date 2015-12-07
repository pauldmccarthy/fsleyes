/*
 * OpenGL fragment shader used for rendering GLVolume instances.
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
 * Texture containing the negative colour map.
 */
uniform sampler1D negColourTexture;

/*
 * Flag which determines whether to 
 * use the negative colour map.
 */
uniform bool useNegCmap;

/*
 * Shape of the imageTexture.
 */
uniform vec3 imageShape;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Transformation matrix to apply to the voxel value,
 * so it can be used as a texture coordinate in the
 * colourTexture.
 */
uniform mat4 voxValXform;

/*
 * Clip voxels below this value. This must be specified
 * in the image texture data range.
 */
uniform float clipLow;

/*
 * Clip voxels above this value. This must be specified
 * in the image texture data range.
 */
uniform float clipHigh;

/*
 * Value in the image texture data range which corresponds
 * to zero - this is used to determine whether to use the 
 * regular, or the negative colour texture (if useNegCmap
 * is true).
 */
uniform float texZero;

/*
 * Invert clipping behaviour - clip voxels
 * that are inside the clipLow/High bounds.
 */
uniform bool invertClip;

/*
 * Image voxel coordinates.
 */
varying vec3 fragVoxCoord;

/*
 * Corresponding image texture coordinates.
 */
varying vec3 fragTexCoord;


void main(void) {

    float voxValue;
    vec4  normVoxValue;
    bool  negCmap  = false;
    vec3  voxCoord = fragVoxCoord;

    /*
     * Skip voxels that are out of the image bounds
     */
    if (!test_in_bounds(voxCoord, imageShape)) {
        
        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }

    /*
     * Look up the voxel value 
     */
    if (useSpline) voxValue = spline_interp(imageTexture,
                                            fragTexCoord,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture,
                                            fragTexCoord).r;

    /*
     * If we are using a negative colour map, 
     * and the voxel value is below the negative 
     * threshold (texZero) invert the voxel 
     * value, and set a flag telling the code
     * below to use the neagtive colour map.
     */
    if (useNegCmap && voxValue <= texZero) {

        negCmap  = true;
        voxValue = texZero + (texZero - voxValue);
    }

    /*
     * Clip out of range voxel values
     */
    if ((!invertClip && (voxValue <  clipLow || voxValue >  clipHigh)) ||
        ( invertClip && (voxValue >= clipLow && voxValue <= clipHigh))) {
      
        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }

    /*
     * Transform the voxel value to a colour map texture
     * coordinate, and look up the colour for the voxel value
     */ 
    normVoxValue = voxValXform * vec4(voxValue, 0, 0, 1);

    if (negCmap) gl_FragColor = texture1D(negColourTexture, normVoxValue.x);
    else         gl_FragColor = texture1D(colourTexture,    normVoxValue.x);
}
