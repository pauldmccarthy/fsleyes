/*
 * OpenGL fragment shader used for rendering GLRGBVolume instances. This
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
{% if textureIs2D %}
uniform sampler2D imageTexture;
{% else %}
uniform sampler3D imageTexture;
{% endif %}

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
 * Shape of the image texture.
 */
uniform vec3 texShape;

/*
 * Use spline interpolation
 */
uniform bool useSpline;

/*
 * Number of values in texture (3 or 4)
 */
uniform int  nvals;

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
    vec4 voxValue;

    if (!test_in_bounds(voxCoord, imageShape)) {
        discard;
    }

    {% if textureIs2D %}
    if (useSpline) {
      voxValue.x = spline_interp(imageTexture, fragTexCoord.xy, texShape.xy, 0);
      voxValue.y = spline_interp(imageTexture, fragTexCoord.xy, texShape.xy, 1);
      voxValue.z = spline_interp(imageTexture, fragTexCoord.xy, texShape.xy, 2);
      voxValue.a = spline_interp(imageTexture, fragTexCoord.xy, texShape.xy, 3);
    }
    else {
      voxValue = texture2D(imageTexture, fragTexCoord.xy);
    }

    {% else %}
    if (useSpline) {
      voxValue.x = spline_interp(imageTexture, fragTexCoord, texShape, 0);
      voxValue.y = spline_interp(imageTexture, fragTexCoord, texShape, 1);
      voxValue.z = spline_interp(imageTexture, fragTexCoord, texShape, 2);
      voxValue.a = spline_interp(imageTexture, fragTexCoord, texShape, 3);
    }
    else {
      voxValue = texture3D(imageTexture, fragTexCoord);
    }
    {% endif %}

    if (nvals == 3)
      voxValue.a = 1;

    gl_FragColor = voxValue;
}
