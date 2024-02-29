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
 * Insertion sort - sorts both the values and indices arrays according
 * to the values. Entries with an index value of -1 are ignored.
 * Insertion sort is stable, which means that the order of equal
 * entries is preserved.
 */
void isort(inout float values[ {{noverlays}}],
           inout int   indices[{{noverlays}}]) {

  int   i, j;
  int   itmp;
  float vtmp;

  /*
   * Move all invalid values (which  have
   * an index of -1) to the end of the list
   */
  for (i = 0, j = 0; i < {{noverlays}}; i++) {
    if (indices[i] == -1) {
      continue;
    }
    values[j]  = values[ i];
    indices[j] = indices[i];
    j          = j + 1;
  }
  while (j < {{noverlays}}) {
    values[ j] = -1;
    indices[j] = -1;
    j          = j + 1;
  }

  for (i = 0; i < {{noverlays}}; i++) {

    /* end of the list */
    if (indices[i] == -1) {
      break;
    }

    vtmp = values[ i];
    itmp = indices[i];
    j    = i - 1;

    while (j >= 0 && values[j] > vtmp) {
      values[ j + 1] = values[ j];
      indices[j + 1] = indices[j];
      j              = j - 1;
    }
    values[ j + 1] = vtmp;
    indices[j + 1] = itmp;
  }
}


void main(void) {

  vec4  rgba;
  int   indices[{{noverlays}}];
  vec4  rgbas[  {{noverlays}}];
  float depths[ {{noverlays}}];

  /* Retrieve RGBA and depth values for every overlay */
  {% for i in range(noverlays) %}
  rgbas[ {{i}}] = texture2D(rgba_{{ i}}, fragTexCoord);
  depths[{{i}}] = texture2D(depth_{{i}}, fragTexCoord).r;
  {% endfor %}

  /*
   * Initialise indices - entries with alpha == 0
   * are ignored, and their index is set to -1,
   * which causes the sort routine to shift them
   * to the back.
   */
  for (int i = 0; i < {{noverlays}}; i++) {
    if (rgbas[i].a == 0) { indices[i] = -1; }
    else                 { indices[i] =  i; }
  }

  /* Sort by depth */
  isort(depths, indices);

  /*
   * Blend RGBA values from all overlays,
   * in order of farthest to nearest.
   */
  rgba = bgColour;
  for (int i = {{noverlays}} - 1; i >= 0; i--) {

    /* Skip transparent values */
    if (indices[i] == -1) {
      continue;
    }

    rgba = ((rgbas[indices[i]] *      rgbas[indices[i]].a) +
            (rgba              * (1 - rgbas[indices[i]].a)));
  }

  /*
   * Set the depth of this fragment to
   * that of the first sorted input depth
   */
  gl_FragColor = rgba;
  gl_FragDepth = depths[0];
}
