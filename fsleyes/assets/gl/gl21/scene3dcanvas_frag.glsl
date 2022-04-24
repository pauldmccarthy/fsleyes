/*
 * Fragment shader used by the Scene3DCanvas to blend multiple overlays
 * together.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * 2D RGBA and depth textures containing the rendered scene for
 * each overlay.
 */
{% for i in range(noverlays) %}
uniform sampler2D rgba_{{i}};
uniform sampler2D depth_{{i}};
{% endfor %}


/* Canvas background colour */
uniform vec4 bgColour;

/* Texture coordinate for this fragment. */
varying vec2 fragTexCoord;


/*
 * Sort both the values and indices arrays according to the values.
 * https://stackoverflow.com/a/749206
 */
void isort(inout float values[ {{noverlays}}],
           inout int   indices[{{noverlays}}]) {

  int   itmp;
  float ftmp;

  for (int i = {{noverlays}} - 1; i >= 0; i--) {
    for (int j = 0; j < i; j++) {
      if (values[i] <= values[j]) {
        ftmp       = values[i];
        values[i]  = values[j];
        values[j]  = ftmp;
        itmp       = indices[i];
        indices[i] = indices[j];
        indices[j] = itmp;
      }
    }
  }
}


void main(void) {

  vec4  rgba;
  int   indices[{{noverlays}}];
  vec4  rgbas[  {{noverlays}}];
  float depths[ {{noverlays}}];

  /* Initialise indices */
  for (int i = 0; i < {{noverlays}}; i++) {
    indices[i] = i;
  }

  /* Retrieve RGBA and depth values for every overlay */
  {% for i in range(noverlays) %}
  rgbas[ {{i}}] = texture2D(rgba_{{ i}}, fragTexCoord);
  depths[{{i}}] = texture2D(depth_{{i}}, fragTexCoord).r;
  {% endfor %}

  /* Sort by depth */
  isort(depths, indices);

  /*
   * Blend RGBA values from all overlays,
   * in order of farthest to nearest.
   */
  rgba = bgColour;
  for (int i = {{noverlays}} - 1; i >= 0; i--) {
    rgba = ((rgbas[indices[i]] *      rgbas[indices[i]].a) +
            (rgba              * (1 - rgbas[indices[i]].a)));
  }

  gl_FragColor = rgba;
  gl_FragDepth = depths[0];
}
