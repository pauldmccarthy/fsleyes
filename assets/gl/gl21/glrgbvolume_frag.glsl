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
 * True if the texture has an alpha channel.
 */
uniform bool hasAlpha;


/*
 * Colour to use for the red channel
 */
uniform vec4 rcolour;


/*
 * Colour to use for the green channel
 */
uniform vec4 gcolour;


/*
 * Colour to use for the blue channel
 */
uniform vec4 bcolour;


/*
 * Scale/offset to apply to the final colour,
 * to adjust brightness/contrast
 */
uniform vec2 colourXform;


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
    vec4  voxValue;
    float alpha;

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

    alpha        = voxValue.a;
    voxValue     = (voxValue.r * rcolour) +
                   (voxValue.g * gcolour) +
                   (voxValue.b * bcolour);
    voxValue.rgb = (voxValue.rgb - 0.5 + colourXform.y) * colourXform.x + 0.5;

    if (hasAlpha)
      voxValue.a *= alpha;

    gl_FragColor = voxValue;
}
